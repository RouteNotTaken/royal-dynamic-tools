#! /usr/bin/env python3
import json
import requests

'''
RoyalTS dynamic folder script.
Used to pull all credentials from a CyberArk personal vault.
Also creates a dynamic credential for any local username configured in CyberArk for a specified host.
Local Username requires the dynamic credential script.

Requirements:
  Folder Custom Properties:
    - cyberArkHostname: FQDN of your CyberArk portal
    - cyberArkSafeName: name of the safe to pull accounts from. Typically your personal safe.

  Credentials:
    - Supply a credential that has read access to the safe being accessed.
'''

HOSTNAME = '$CustomProperty.cyberArkHostname$'
SAFE_NAME = '$CustomProperty.cyberArkSafeName$'
LDAP_CREDENTIAL = {
    'username': '$EffectiveUsername$',
    'password': '$EffectivePassword$',
}


def ca_login(hostname, ldap_credential):
    '''
    Login to CyberArk API and return session token.
    Currently only supports LDAP auth.
    '''
    login_url = f'{hostname}/PasswordVault/API/auth/LDAP/Logon'
    headers = {'Content-Type': 'application/json'}
    payload = ldap_credential
    r = requests.post(login_url, headers=headers, json=payload)

    # Raise error if response not 200
    r.raise_for_status()
    return r.json()


def ca_logout(hostname, api_key):
    '''Logout CyberArk API session associated with given api key. Returns HTTP response text'''
    logout_url = f'{hostname}/PasswordVault/API/Auth/Logoff'
    headers = {'Authorization': api_key}
    r = requests.post(logout_url, headers=headers)
    return r.text


def get_ca_account_ids_from_safe(hostname, api_key, safe_name):
    '''Returns list of dicts for every account in a CyberArk safe.'''
    account_url = f'{hostname}/PasswordVault/API/accounts?filter= SafeName eq {safe_name}'
    headers = {'Authorization': api_key}
    r = requests.get(account_url, headers=headers)

    # Raise error if response not 200
    r.raise_for_status()
    ids = []
    for i in r.json()['value']:
        ids.append(
            {
                'id': i['id'],
                'username': i['userName'],
                'secret_type': i['secretType'],
            }
        )
    return ids


def get_ca_password(hostname, api_key, account_id):
    '''
    Returns password for supplied account id.
    Password returned as quoted string. Example: "MyPassword"
    '''
    password_url = f'{hostname}/PasswordVault/API/accounts/{account_id}/Password/Retrieve'
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json',
        }
    payload = {
        'reason': 'RoyalTS Dynamic Credential',
        'ActionType': 'show',
    }
    r = requests.post(password_url, headers=headers, json=payload)
    # Raise error if response not 200
    r.raise_for_status()
    return r.json()


def main():
    hostname = f'https://{HOSTNAME}'
    api_key = ca_login(hostname, LDAP_CREDENTIAL)
    account_ids = get_ca_account_ids_from_safe(hostname, api_key, SAFE_NAME)

    rjson = {
        "Objects": [
            {
                "Type": "DynamicCredential",
                "Name": "CA local account",
            }
        ]
    }

    for cred in account_ids:
        rjson['Objects'].append(
            {
                "Type": "Credential",
                "Name": cred['username'],
                "Username": cred['username'],
                "Password": get_ca_password(hostname, api_key, cred['id'])
            }
        )
    print(json.dumps(rjson))


if __name__ == "__main__":
   main() 