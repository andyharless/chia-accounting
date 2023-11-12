import requests
import urllib3
import json
import os
import sys
import pandas as pd
from datetime import datetime

REPO_ROOT = '..'
coderoot = os.getenv("CHIA_CODE_ROOT")
if coderoot is None:
    coderoot = '../..'
sys.path.append(coderoot)
sys.path.append(REPO_ROOT)

from time import sleep
from local_data import cert_path

WAIT_INTERVAL = 2
WAIT_COMPLAIN = 10

cert = (cert_path + '/private_wallet.crt', 
        cert_path + '/private_wallet.key')

# TODO: Deal with failure conditions
# TODO: Allow alternative ports


urllib3.disable_warnings()



def get_block_records(start=0, end=20, cert=cert):
                     
    return pd.json_normalize(json.loads(requests.post(
                "https://localhost:8555/get_block_records",
                data=f'{{"start": {start}, "end": {end} }}', 
                headers={'Content-Type': 'application/json'}, 
                cert=cert, verify=False
            ).text)['block_records'])


def get_block_times(start=0, end=20, cert=cert):
                     
    df = pd.json_normalize(json.loads(requests.post(
                "https://localhost:8555/get_block_records",
                data=f'{{"start": {start}, "end": {end} }}', 
                headers={'Content-Type': 'application/json'}, 
                cert=cert, verify=False
            ).text)['block_records'])[['height', 'timestamp']].dropna()

    df['time'] = pd.to_datetime(df.timestamp, unit='s')
    
    return df.drop(columns=['timestamp'])


def get_block_time(height=4000000, cert=cert):

    result = json.loads(requests.post(
                "https://localhost:8555/get_block_record_by_height",
                data=f'{{"height": {height}}}', 
                headers={'Content-Type': 'application/json'}, 
                cert=cert, verify=False
            ).text)['block_record']['timestamp']
                     
    return pd.NaT if result is None else datetime.fromtimestamp(result)

