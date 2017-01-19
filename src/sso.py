
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

def validate_token(refresh_token):
    DECRYPTED = boto3.client('kms').decrypt(CiphertextBlob=b64decode(SSO_BASIC_AUTH_PASSWORD))['Plaintext']
    task_url = "service/oauth2/access_token?realm=SungardAS"
    url = "https://%s/%s"%(SSO_HOST, task_url)
    client_auth = requests.auth.HTTPBasicAuth(SSO_BASIC_AUTH_USERNAME, DECRYPTED)
    post_data = {'grant_type':'refresh_token', 'refresh_token':refresh_token}
    r = requests.post(url, auth=client_auth, data=post_data, verify=False)
    return r._content
