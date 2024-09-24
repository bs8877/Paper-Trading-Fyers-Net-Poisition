from flask import Flask, request
from fyers_apiv3 import fyersModel
import threading

# Replace these with your actual Fyers API credentials
client_id = "G7PM6ZVJGQ-100"
secret_key = "5T4KKYA6CR"
redirect_uri = "http://localhost:5000/callback"
response_type = "code"

# Initialize the session
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type
)

app = Flask(__name__)

@app.route('/')
def index():
    # Step 1: Generate the authentication code URL
    auth_code_url = session.generate_authcode()
    return f'<a href="{auth_code_url}">Click here to authorize the application</a>'

@app.route('/callback')
def callback():
    # Step 2: Capture the authorization code
    auth_code = request.args.get('code')
    if auth_code:
        # Generate access token using the authorization code
        token_response = session.generate_token(auth_code)
        return f"Access Token Response: {token_response}"
    return "Authorization code not found."

def run_server():
    app.run(port=5000)

# Run the Flask server in a separate thread
if __name__ == '__main__':
    threading.Thread(target=run_server).start()
