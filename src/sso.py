
import requests
import os
import boto3
from base64 import b64decode

SSO_HOST = os.environ['SSO_HOST']
SSO_BASIC_AUTH_USERNAME = os.environ['SSO_BASIC_AUTH_USERNAME']
SSO_BASIC_AUTH_PASSWORD = os.environ['SSO_BASIC_AUTH_PASSWORD']
SSO_API_GRANT_TYPE = 'password';
SSO_SCOPE = 'openid phone address email profile cloud';
SSO_TASK_URL = "/service/oauth2/access_token?realm=SungardAS";

def authenticate(username, password):
    DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(SSO_BASIC_AUTH_PASSWORD))['Plaintext']
    task_url = "service/oauth2/access_token?realm=SungardAS"
    url = "https://%s/%s"%(SSO_HOST, task_url)
    client_auth = requests.auth.HTTPBasicAuth(SSO_BASIC_AUTH_USERNAME, DECRYPTED)
    post_data = {"grant_type": SSO_API_GRANT_TYPE, "username": username, "password": password, "scope": SSO_SCOPE}
    r = requests.post(url, auth=client_auth, data=post_data, verify=False)
    return r._content

def validate_token(access_token):
    DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(SSO_BASIC_AUTH_PASSWORD))['Plaintext']
    task_url = "service/oauth2/tokeninfo?realm=SungardAS"
    url = "https://%s/%s"%(SSO_HOST, task_url)
    payload = {"access_token": access_token}
    r = requests.get(url, params=payload, verify=False)
    return r._content
    """
    {"phone":"","scope":["phone","address","email","cloud","openid","profile"],"grant_type":"password","address":"","email":"","realm":"SungardAS","cloud":"","openid":"","token_type":"Bearer","expires_in":1,"access_token":"52d8088a-...","profile":""}
    {"error":"invalid_request","error_description":"Access Token not valid"}
    """

def extend_token(refresh_token):
    DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(SSO_BASIC_AUTH_PASSWORD))['Plaintext']
    task_url = "service/oauth2/access_token?realm=SungardAS"
    url = "https://%s/%s"%(SSO_HOST, task_url)
    client_auth = requests.auth.HTTPBasicAuth(SSO_BASIC_AUTH_USERNAME, DECRYPTED)
    post_data = {'grant_type':'refresh_token', 'refresh_token':refresh_token}
    r = requests.post(url, auth=client_auth, data=post_data, verify=False)
    return r._content

def find_user_detail(access_token):
    DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(SSO_BASIC_AUTH_PASSWORD))['Plaintext']
    task_url = "/service/oauth2/userinfo?realm=SungardAS"
    url = "https://%s/%s"%(SSO_HOST, task_url)
    access_token = "Bearer " + access_token
    headers = {"Authorization" : access_token, "Content-Type" : "application/json"}
    r = requests.get(url, headers=headers, verify=False)
    return r._content
    """
    {
        "zoneinfo":"America/New_York",
        "guid":"b2fc88a6-...",
        "company_guid":"7ec344ba-...",
        "phone":"",
        "sub":"alex.ough@sungardas.com",
        "updated_at":"0",
        "email":"alex.ough@sungardas.com",
        "roles":[],
        "family_name":"Ough",
        "applications":[],
        "given_name":"Alex",
        "groups":[],
        "userGuid":"b2fc88a6-..."
    }
    """
