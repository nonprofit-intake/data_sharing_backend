import os
import json
import math
import pandas as pd
import psycopg2
import cryptography
from chalice import Chalice, BadRequestError
from cryptography.fernet import Fernet

# initialize Chalice app
app = Chalice(app_name='data-sharing-api')

# initialize Fernet suite
encryption_key = str.encode(os.environ["ENCRYPTION_KEY"])
fernet = Fernet(encryption_key)

# assign environment variables
DB_HOST = os.environ['DB_HOST']
DB_USER = os.environ['DB_USER']
DB_PWD = os.environ['DB_PWD']
WEB_PWD = os.environ['WEB_PWD']

# helper functions
def decipher(cipher_string):
    deciphered_string = fernet.decrypt(str.encode(cipher_string)).decode("utf-8")
    return deciphered_string

def wrangle(df):
    """
    Wrangles data for use in matching function.
    """
    wrangled_df = df.copy()
    
    # decipher SSNs
    wrangled_df['ssn'] = wrangled_df['ssn'].apply(lambda row_value: int(decipher(row_value)) if pd.notnull(row_value) else math.nan)

    # format date strings for readability
    wrangled_df['enroll_date'] = wrangled_df['enroll_date'].apply(lambda row_value: row_value.strftime("%m-%d-%Y") if pd.notnull(row_value) else math.nan)
    wrangled_df['exit_date'] = wrangled_df['exit_date'].apply(lambda row_value: row_value.strftime("%m-%d-%Y") if pd.notnull(row_value) else math.nan)

    return wrangled_df

def find_matches(df, request_body):
    """
    Assumes all records in input dataframe are partial matches until matched.
    Compares request body and input dataframe for matching last_name and SSN.
    Returns two dataframes in JSON format: full and partial matches.
    """
    guest_data = tuple(zip(request_body["last_name"], request_body["ssn"]))

    full_match_dfs = []
    all_partial_matches = df.copy()

    for last_name, ssn in guest_data:
        if ((all_partial_matches["last_name"] == last_name) & (all_partial_matches["ssn"] == ssn)).any():
            full_match = df[(df["last_name"] == last_name) & (df["ssn"] == ssn)]
            full_match_dfs.append(full_match)
            
            all_partial_matches.drop(full_match.index, inplace=True)

    all_full_matches = pd.concat(full_match_dfs)

    # drop ssn columns
    all_full_matches.drop(columns='ssn', inplace=True)
    all_partial_matches.drop(columns='ssn', inplace=True)

    # convert datfarames to JSON format
    fm_json = all_full_matches.to_json(orient="records")
    pm_json = all_partial_matches.to_json(orient="records")

    return fm_json, pm_json


# routes
@app.route('/')
def index():
    return {'Status': 'OK'}


@app.route('/guests', methods=['POST'])
def match_guests():
    request_body = app.current_request.json_body

    # convert all request names to lowercase; last names in database are lowercase
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
            where_clause = f"WHERE last_name='{lowered_last_names[0]}'"
        else:
            where_clause = f"WHERE last_name IN {tuple(lowered_last_names)}"

        query = f"""SELECT first_name, last_name, ssn, enroll_date, exit_date, exit_destination, income_at_entry, income_at_exit 
                    FROM guestsdev 
                    {where_clause}"""

        # creates dataframe from query results (automatically drops connection)
        with psycopg2.connect(host=DB_HOST, user=DB_USER, password=DB_PWD) as connection:
            df = pd.read_sql_query(query, connection)

        # wrangle data for matching
        wrangled_df = wrangle(df)

        # find last_names not found in database
        table_last_names = wrangled_df['last_name'].unique()
        no_match_found = list(set(lowered_last_names) - set(table_last_names))

        # retrieve full and partial matching dataframes
        full_matches, partial_matches = find_matches(wrangled_df, request_body)

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
