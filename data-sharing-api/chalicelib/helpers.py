import os
import math
import pandas as pd
from cryptography.fernet import Fernet

# initialize Fernet suite
encryption_key = str.encode(os.environ["ENCRYPTION_KEY"])
fernet = Fernet(encryption_key)

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