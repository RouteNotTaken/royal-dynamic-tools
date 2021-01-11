import json
import requests

'''
RoyalTS dynamic credential script, used by royal Cyber Ark dynamic folder script.
Used to pull username/password ad hoc for a Royal connection.
Searches CyberArk for an account that maches the hostname of the connection.

Requirements:
  RoyalTSX Version: 5.0.0+
  Credentials:
    - Supply a credential that has read access to the safe being accessed.
'''
HOSTNAME = '$CustomProperty.cyberArkHostname$'
LDAP_CREDENTIAL = {
    'username': '$EffectiveUsername$',
    'password': '$EffectivePassword$',
}


def ca_login(hostname, ldap_credential):
    '''
    Login and return session token.
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


def get_ca_account_id(hostname, api_key, address_name):
    '''
    Search CyberArk for an account that starts with the supplied hostname.
    Return account id and username within a dictionary.
    '''
    account_url = f'{hostname}/PasswordVault/API/accounts?searchtype=startswith&search={address_name}&limit=1'
    headers = {'Authorization': api_key}
    r = requests.get(account_url, headers=headers)
    # Raise error if response not 200
    r.raise_for_status()
    return {
        'id': r.json()['value'][0]['id'],
        'username': r.json()['value'][0]['userName'],
    }


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
    return r.text


def main():
    hostname = f'https://{HOSTNAME}'
    address_name = '$Target.Name$' #Target.Name token returns computer name of the RoyalTS connection being established
    api_key = ca_login(hostname, LDAP_CREDENTIAL)
    account = get_ca_account_id(hostname, api_key, address_name)
    credential = get_ca_password(hostname, api_key, account['id'])

    rjson = {
        "Username": account['username'],
        "Password": credential.strip('"')
    }

    print(json.dumps(rjson))


if __name__ == "__main__":
   main() 