#! /usr/bin/env python3
import json
import requests

'''
RoyalTS dynamic folder script.
Pulls all devices from a LibreNMS server and returns as Royal Connections.

All hosts returned as terminal(SSH) connections.

Requirements:
  Folder Custom Properties:
    - libreHostname: FWDN of the target LibreNMS server
    - libreAPIKey: API Key with read access to the LibreNMS server
'''

HOSTNAME = '$CustomProperty.libreHostname$' 
API_KEY = '$CustomProperty.libreAPIKey$'

def get_libre_devices(hostname, api_key):
    '''Return json reponse of all devices configured in LibreNMS'''
    uri = f'http://{hostname}/api/v0/devices'
    headers = {'X-Auth-Token': api_key}
    response = requests.request('GET', uri, headers=headers)

    # Raise error if response not 200
    response.raise_for_status()

    return response.json()['devices']


def cleanup_devices(devices):
    '''
    Cleanup function to remove or rename devices returned by LibreNMS.
    Currently removes all linux and panos devices.
    '''
    hosts = []
    for d in devices:
        if 'nux' not in d['os'] and 'pan' not in d['os']:
            hosts.append({
                'name': d['hostname'],
                'ip': d['ip'],
            })
    return hosts


def convert_to_rjson(devices):
    '''
    Return single ssh connections in the root object.
    Type set to SSH by default.
    ComputerName returned as static IP of the host.
    '''
    rjson = {
        'Objects': []
    }
    for d in devices:
        rjson['Objects'].append(
            {
                "Type": "TerminalConnection",
                "TerminalConnectionType": "SSH",
                "Name": d['name'],
                "ComputerName": d['ip'],
                "CredentialsFromParent": True,
            }
        )
    return rjson



def main():
    rjson = convert_to_rjson((cleanup_devices(get_libre_devices(HOSTNAME, API_KEY))))
    print(json.dumps(rjson))

if __name__ == "__main__":
    main()