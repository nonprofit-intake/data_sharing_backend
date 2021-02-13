import os
import json
import math
import pandas as pd
import psycopg2-binary
import cryptography
from chalice import Chalice, BadRequestError

app = Chalice(app_name='data-sharing-api')

HOST = os.environ['HOST']
USER = os.environ['USER']
PASSWORD = os.environ['PASSWORD']
AUTH_PWD = os.environ['AUTH_PWD']
ENCRYPTION_KEY = str.encode(os.environ["ENCRYPTION_KEY"])


@app.route('/')
def index():
    return {'Status': 'OK'}

@app.route('/guests', methods=['POST'])
def match_guests():
    request_body = app.current_request.json_body
    if request_body:
        try:
            assert isinstance(request_body["pwd"], str), "'pwd' must be a string type"
            assert request_body["pwd"] == AUTH_PWD, "Incorrect password"
            assert isinstance(request_body, dict), "JSON object must be a dictionary"
            assert "last_name" in request_body.keys(), "Input JSON object requires last_name key"
            assert "ssn" in request_body.keys(), "Input JSON object requires ssn key"
            assert isinstance(request_body["last_name"], list), "'last_name' key must contain a list"
            assert isinstance(request_body["ssn"], list), "'snn' key must contain a list"
            assert len(request_body["last_name"]) == len(request_body["ssn"]), "ValueError: 'last_name' and 'ssn' lists must be of equal length"
            assert request_body["last_name"], "'last_name' key must not be an empty list"
            assert request_body["ssn"], "'ssn' key must not be an empty list"
            assert all(isinstance(last_name, str) for last_name in request_body["last_name"]), "'last_name' values must all be of type string"
            assert all(isinstance(ssn, str) for ssn in request_body["ssn"]), "'ssn' values must all be of type string"

        except AssertionError as error:
            raise BadRequestError(str(error))

        try:
            lower_last_names = [name.lower() for name in request_body['last_name']]
            
            if len(lower_last_names) == 1:
            query = f"SELECT * FROM guestsdev WHERE last_name='{lower_last_names[0]}'"
            else:
            query = f"SELECT * FROM guestsdev WHERE last_name IN {tuple(lower_last_names)}"

            # creates a dataframe from the results of the query
            with psycopg2.connect(host=HOST,user=USER,password=PASSWORD) as connection:
            df = pd.read_sql_query(query, connection)

            # wrangling to remove index, create readable ssn, str format of enroll and exit date
            df.drop(columns="index", inplace=True)
            df['ssn'] = df['ssn'].apply(lambda row: b"".join(row) if pd.notnull(row) else math.nan)
            df['enroll_date'] = df['enroll_date'].apply(lambda row: row.strftime("%m-%d-%Y") if pd.notnull(row) else math.nan)
            df['exit_date'] = df['exit_date'].apply(lambda row: row.strftime("%m-%d-%Y") if pd.notnull(row) else math.nan)
            
            def find_matches(df):
                '''Find last names in returned query that match request_body last names/
                If it's a match for the last name, check that it's a match for SSN.
                '''
                # create a copy of df
                df = df.copy()

                # drop where ssn is nan
                df.dropna(subset=['ssn'], inplace=True)
                df['match'] = False
                
                for i, req_last_name in enumerate(lower_last_names):
                for j, row_last_name in enumerate(df['last_name']):
                        # if df row is equal to request value
                        if row_last_name == req_last_name:
                            # set match value equal to true instead
                            df['match'].iloc[j] = bcrypt.checkpw(request_body['ssn'][i].encode('utf8'), df['ssn'].iloc[j])
                
                df.drop(columns='ssn', inplace=True)
            
                return df

            # call the find match function and create a new df of both true/false matches
            match_df = find_matches(df)

            df_true = match_df[match_df['match'] == True].drop(columns='match')
            df_false = match_df[match_df['match'] == False].drop(columns='match')
        
            res_true = df_true.to_json(orient="records")
            res_false = df_false.to_json(orient="records")
            
            res = {'complete_matches': json.loads(res_true),
                'partial_matches': json.loads(res_false)}
            res_json = json.dumps(res)

            final = json.loads(res_json)
            return final

        except (Exception, psycopg2.Error) as error:
            raise BadRequestError(str(error))