import os
import json
import math
import pandas as pd
import psycopg2-binary
import cryptography
from chalice import Chalice

app = Chalice(app_name='data-sharing-api')

HOST = os.environ['HOST']
USER = os.environ['USER']
PASSWORD = os.environ['PASSWORD']
AUTH_PWD = os.environ['AUTH_PWD']
ENCRYPTION_KEY = str.encode(os.environ["ENCRYPTION_KEY"])


@app.route('/')
def index():
    return {'Status': 'OK'}

# @app.route('/guests')