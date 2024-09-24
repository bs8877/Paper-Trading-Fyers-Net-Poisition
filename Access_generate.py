from fyers_apiv3 import fyersModel

client_id = "YOUR_CLIENT_ID"
secret_key = "YOUR_SECRET_KEY"
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
response_type = "code"
grant_type = "authorization_code"

auth_code = "YOUR_AUTH_CODE" #INPUT AUTH CODE GENERATE FROM FYERS API 

session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type,
    grant_type=grant_type
)

session.set_token(auth_code)

response = session.generate_token()
print(response)