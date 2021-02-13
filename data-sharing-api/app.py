import os
import json
import math
import pandas as pd
import psycopg2
import cryptography
from chalice import Chalice, BadRequestError
from cryptography.fernet import Fernet, InvalidToken

# initialize Chalice app
app = Chalice(app_name='data-sharing-api')
app.debug = True # ONLY FOR DEVELOPMENT

# initialize Fernet suite
encryption_key = str.encode(os.environ["ENCRYPTION_KEY"])
fernet = Fernet(encryption_key)

# assign environment variables
HOST = os.environ['HOST']
USER = os.environ['USER']
PASSWORD = os.environ['PASSWORD']
AUTH_PWD = os.environ['AUTH_PWD']
ENCRYPTION_KEY = str.encode(os.environ["ENCRYPTION_KEY"])

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
    df['ssn'] = df['ssn'].apply(lambda row_value: decipher(row_value) if pd.notnull(row_value) else math.nan)

    # format date strings for readability
    df['enroll_date'] = df['enroll_date'].apply(lambda row_value: row_value.strftime("%m-%d-%Y") if pd.notnull(row_value) else math.nan)
    df['exit_date'] = df['exit_date'].apply(lambda row_value: row_value.strftime("%m-%d-%Y") if pd.notnull(row_value) else math.nan)

    return wrangled_df

def find_matches(df, request_body, req_last_names):
    """
    Find last names in query dataframe that match request_body last names.
    If it's a match for the last name, check that it's a match for SSN.
    """
    match_df = df.copy()

    # drop records where ssn is nan
    match_df.dropna(subset=['ssn'], inplace=True)
    match_df['match'] = False
    
    # if record data is equal to request value, set match value equal to true
    for i, req_last_name in enumerate(req_last_names):
        for j, row_last_name in enumerate(match_df['last_name']):
                if row_last_name == req_last_name and request_body['ssn'][i] == match_df['ssn'].iloc[j]:
                    match_df['match'].iloc[j] = True
        
    match_df.drop(columns='ssn', inplace=True)

    return match_df


# routes
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
            # convert all request names to lowercase, last names in database are lowercase
            req_last_names = [name.lower() for name in request_body['last_name']]
            
            if len(req_last_names) == 1:
                query = f"""SELECT ssn, enroll_date, exit_date, exit_destination, first_name, income_at_entry, income_at_exit, last_name
                            FROM guestsdev 
                            WHERE last_name='{req_last_names[0]}'"""
            else:
                query = f"""SELECT ssn, enroll_date, exit_date, exit_destination, first_name, income_at_entry, income_at_exit, last_name 
                            FROM guestsdev 
                            WHERE last_name IN {tuple(req_last_names)}"""

            # creates  dataframe from query results (automatically drops connection)
            with psycopg2.connect(host=HOST,user=USER,password=PASSWORD) as connection:
                df = pd.read_sql_query(query, connection)

            # wrangle data for matching
            wrangled_df = wrangle(df)

            # create match column
            match_df = find_matches(wrangled_df, request_body, req_last_names)

            # create dataframes for complete and partial matches
            df_true = match_df[match_df['match'] == True].drop(columns='match')
            df_false = match_df[match_df['match'] == False].drop(columns='match')
        
            # convert dataframes to JSON format and send as response
            res_true = df_true.to_json(orient="records")
            res_false = df_false.to_json(orient="records")
            
            raw_response = {'complete_matches': json.loads(res_true),
                'partial_matches': json.loads(res_false)}
            
            dumped_response = json.dumps(raw_response)
            final_response = json.loads(dumped_response)
            
            return final_response

        except (Exception, psycopg2.Error) as error:
            raise BadRequestError(str(error))
