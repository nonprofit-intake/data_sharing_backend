import os
import json
import pandas as pd
import psycopg2
from chalice import Chalice, BadRequestError
from chalicelib import helpers

# initialize Chalice app
app = Chalice(app_name='data-sharing-api')

# assign environment variables
DB_HOST = os.environ['DB_HOST']
DB_USER = os.environ['DB_USER']
DB_PWD = os.environ['DB_PWD']
WEB_PWD = os.environ['WEB_PWD']


@app.route('/')
def index():
    return {'Status': 'OK'}


@app.route('/guests', methods=['POST'])
def match_guests():
    request_body = app.current_request.json_body

    # convert all request names to lowercase
    lowered_last_names = [name.lower() for name in request_body['last_name']]
    request_body["last_name"] = lowered_last_names

    try:
        assert isinstance(request_body["pwd"], str), "'pwd' must be a string type"
        assert request_body["pwd"] == WEB_PWD, "Incorrect password"
        assert isinstance(request_body, dict), "JSON object must be a dictionary"
        assert "last_name" in request_body.keys(), "Input JSON object requires last_name key"
        assert "ssn" in request_body.keys(), "Input JSON object requires ssn key"
        assert isinstance(request_body["last_name"], list), "'last_name' key must contain a list"
        assert isinstance(request_body["ssn"], list), "'snn' key must contain a list"
        assert len(request_body["last_name"]) == len(request_body["ssn"]), "ValueError: 'last_name' and 'ssn' lists must be of equal length"
        assert request_body["last_name"], "'last_name' key must not be an empty list"
        assert request_body["ssn"], "'ssn' key must not be an empty list"
        assert all(isinstance(last_name, str) for last_name in request_body["last_name"]), "'last_name' values must all be of type string"
        assert all(isinstance(ssn, int) for ssn in request_body["ssn"]), "'ssn' values must be integers"

    except AssertionError as error:
        raise BadRequestError(str(error))

    try:
        # define query based on length of last name list
        if len(lowered_last_names) == 1:
            where_clause = f"WHERE LOWER(last_name)='{lowered_last_names[0]}'"
        else:
            where_clause = f"WHERE LOWER(last_name) IN {tuple(lowered_last_names)}"

        query = f"""SELECT LOWER(first_name) as first_name, LOWER(last_name) as last_name, ssn, enroll_date, exit_date, exit_destination, income_at_entry, income_at_exit 
                    FROM guests
                    {where_clause}"""

        # creates dataframe from query results (automatically drops connection)
        with psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PWD) as connection:
            df = pd.read_sql_query(query, connection)

        print(df.shape)
        # wrangle data for matching
        wrangled_df = helpers.wrangle(df)

        # find last_names not found in database
        table_last_names = wrangled_df['last_name'].unique()
        no_match_found = list(set(lowered_last_names) - set(table_last_names))

        # retrieve full and partial matching dataframes
        full_matches, partial_matches = helpers.find_matches(wrangled_df, request_body)

        raw_response = {
            'full_matches': json.loads(full_matches),
            'partial_matches': json.loads(partial_matches),
            'no_match_found': no_match_found,
            }
        
        dumped_response = json.dumps(raw_response)
        final_response = json.loads(dumped_response)
        
        return final_response

    except (Exception, psycopg2.Error) as error:
        raise BadRequestError(str(error))
