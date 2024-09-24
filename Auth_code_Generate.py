from fyers_apiv3 import fyersModel 

client_id = "YOUR_CLIENT_ID"  #INPUT CLIENT ID FROM FYERS API 
secret_key = "YOUR_SECRET_KEY" #INPUT SECRET KEY FROM FYERS API
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
response_type = "code"

session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type
)

response = session.generate_authcode()
print(response)
