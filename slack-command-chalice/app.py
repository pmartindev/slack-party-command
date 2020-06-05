import os
import logging
import slack
import re
from math import floor
from random import choice
from slack.errors import SlackApiError
import json
from urllib.parse import urlparse, parse_qs
from chalice import Chalice, Rate, Response

# Grab the API token and Verification token from the environment variables assigned in the 
# Chalice config
API_TOKEN = os.environ["API_TOKEN"]
VERIFICATION_TOKEN = os.environ["VERIFICATION_TOKEN"]

#  Create Chalice's app, and turn on chalice features
app = Chalice(app_name='party-slackbot')
app.debug = True
app.api.cors = True

# Define logging
logger = logging

# Default route / with only method POST. MUST specify content type
@app.route('/',methods=['POST'], content_types=['application/x-www-form-urlencoded'])
def index():
    # Grab the request data and parse as a dictionary
    request_body = parse_qs(app.current_request.raw_body.decode('utf-8'))
    
    response_body = {}
    # Define the payload type for the response
    headers = {'Content-Type': 'application/json'}

    if request_body['token'][0] == os.environ['VERIFICATION_TOKEN']:
        response_code = 200
    else:
        response_body['error'] = 'Unauthorized'
        response_code = 401

    try: 
        make_slack_request(request_body)
    except SlackApiError as error:
        assert error.response["ok"] is False
        assert error.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        response_body = {}
        response_body['success'] = False
        response_body['error'] = error.response['error']
        response_code = 400

    # Return the appropriate response
    body = ''
    if response_code != 200:
        body = response_body
    return Response(status_code=response_code, body = body, headers=headers)


# Default route / with only method POST. MUST specify content type
@app.route('/party-gen',methods=['POST'], content_types=['application/x-www-form-urlencoded'])
def generate_party_emoji():
    # Grab the request data and parse as a dictionary
    request_body = parse_qs(app.current_request.raw_body.decode('utf-8'))
    
    response_body = {}
    # Define the payload type for the response
    headers = {'Content-Type': 'application/json'}

    if request_body['token'][0] == os.environ['VERIFICATION_TOKEN']:
        response_code = 200
    else:
        response_body['error'] = 'Unauthorized'
        response_code = 401

    try: 
        make_slack_request(request_body)
    except SlackApiError as error:
        assert error.response["ok"] is False
        assert error.response["error"]  # str like 'invalid_auth', 'channel_not_found'
        response_body = {}
        response_body['success'] = False
        response_body['error'] = error.response['error']
        response_code = 400

    # Return the appropriate response
    body = ''
    if response_code != 200:
        body = response_body
    return Response(status_code=response_code, body = body, headers=headers)

def make_slack_request(request_body: dict):
    # Initializes the slack with the appropriate API_TOKEN
    client = slack.WebClient(token=API_TOKEN)

    channel_id = request_body['channel_id'][0]
    text = request_body['text'][0]
    party_text =  generate_party_text(
            slack_client = client, 
            text = text, 
            channel_id=channel_id
        )
    response = client.chat_postMessage(
        channel=channel_id,
        text = party_text
    )
    return response

def generate_party_text(slack_client, text: str, channel_id) -> str:
    emoji_response = slack_client.emoji_list()
    party_emoji_list = []
    slack_message_text = ""
    party_items = re.search(r'\d+', text).group()
    party_text = re.search(r'(?<=")[^"]*(?=")', text).group()
    for emoji_name in emoji_response["emoji"].keys():
        if emoji_name.startswith("party_"):
            party_emoji_list.append(emoji_name)
    for i in range(int(party_items)):
        if i == floor(int(party_items)/2):
            slack_message_text += party_text + " "
        slack_message_text += ":" + choice(party_emoji_list) + ": "        
    return slack_message_text
