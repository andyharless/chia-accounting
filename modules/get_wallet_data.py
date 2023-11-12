import requests
import urllib3
import json
import os
import sys
import pandas as pd

REPO_ROOT = '..'
coderoot = os.getenv("CHIA_CODE_ROOT")
if coderoot is None:
    coderoot = '../..'
sys.path.append(coderoot)
sys.path.append(REPO_ROOT)

from time import sleep
from local_data import cert_path
from .get_block_data import get_block_time

WAIT_INTERVAL = 2
WAIT_COMPLAIN = 10

cert = (cert_path + '/private_wallet.crt', 
        cert_path + '/private_wallet.key')

# TODO: Deal with failure conditions


urllib3.disable_warnings()


def log_in_and_sync(wallet=None, cert=cert, interval=WAIT_INTERVAL,
                    complain=WAIT_COMPLAIN):

    if wallet is not None:
        fingerprint = os.getenv(wallet)
        if fingerprint != json.loads(requests.post(
                    "https://localhost:9256/get_logged_in_fingerprint",
                    data='{}', headers={'Content-Type': 'application/json'}, 
                    cert=cert, verify=False
                    ).text)['fingerprint']:
            requests.post(
                    "https://localhost:9256/log_in",
                    data=f'{{"fingerprint": {fingerprint}}}',
                    headers={'Content-Type': 'application/json'}, 
                    cert=cert, verify=False)
            wait = 0
            while not json.loads(requests.post(
                    "https://localhost:9256/get_sync_status",
                    data='{}', headers={'Content-Type': 'application/json'}, 
                    cert=cert, verify=False
                        ).text)['synced']:
                wait += interval
                if not wait % complain:
                    print(f'Waited {wait} seconds for sync...')
                sleep(interval)
            
            return None
            
            
def get_coin_records(wallet=None, cert=cert):
                     
    log_in_and_sync(wallet=wallet, cert=cert)

    return pd.json_normalize(json.loads(requests.post(
                "https://localhost:9256/get_coin_records",
                data='{}', headers={'Content-Type': 'application/json'}, 
                cert=cert, verify=False
            ).text)['coin_records']).drop(
            columns=['metadata', 'type']).rename(
            columns={'wallet_identifier.id':'wallet', 
                 'wallet_identifier.type':'wallet_type'})

                 
def get_transactions(coin_records):

    spends = coin_records[coin_records.spent_height > 0].copy()
    spends['block'] = spends.spent_height
    spends['type'] = 'spent'
    spends['delta'] = -spends.amount

    receipts = coin_records.copy()
    receipts['block'] = receipts.confirmed_height
    receipts['type'] = 'recieved'
    receipts['delta'] = receipts.amount

    return pd.concat([spends, receipts]).sort_values('block')
    

def get_cat_names(wallet=None, cert=cert):
                     
    log_in_and_sync(wallet=wallet, cert=cert)

    wallets = json.loads(requests.post(
                "https://localhost:9256/get_wallets",
                data='{"include_data": false}', 
                headers={'Content-Type': 'application/json'}, 
                cert=cert, verify=False).text)['wallets']                 

    namelist = [None] * (max(w['id'] for w in wallets) + 1)
    for w in wallets:
        namelist[w['id']] = w['name']
    
    return namelist
    chia_accounting
    
def get_cat_symbol(name):

    if name is None:
        return None
    if name[:4] == 'Chia':
        return 'Chia'
    elif '(' in name and ')' in name:
        return name.split('(')[1].split(')')[0]
    elif 'Wallet' in name:
        return name[:3]
    else:
        return name[:7]
        
        
def get_cat_symbols(cat_names):
    
    return [get_cat_symbol(name) for name in cat_names]


def get_xch_balances(wallet=None, cert=cert):

    XCH = 1
    df = get_transactions(get_coin_records(wallet, cert=cert))
    xch = df[df.wallet == XCH][['block', 'delta']].copy()
    xch['balance'] = xch.delta.cumsum() / 1e12
    xch['time'] = xch.block.apply(lambda x: get_block_time(x))
    return xch[['time', 'balance']]
    
