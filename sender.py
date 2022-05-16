# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Original file obtained from: https://github.com/googleworkspace/python-samples/blob/master/gmail/quickstart/quickstart.py
# Used to make the connection with the API
# Modified to achieve what was needed

from __future__ import print_function
import os.path
import email
import email.mime.text
import base64
import string
import requests
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Function to send an email, made so that the function could be called from another function just one time
def email_sequence(patient_email, ap_time, ap_date, creds_gmail):
    # connects to the API
    service = build('gmail', 'v1', credentials=creds_gmail)
    send_message(service, b'me', create_message(patient_email, ap_time, ap_date))

# Function that creates the message to be sent
def create_message(patient_email, ap_time, ap_date):
    # opens the html template to send it
    with open('templates\email_template.html', 'r') as opener:
        text = opener.read()
    text = str(text)
    # formats the text so that the date and time is specified for each mail
    text = text.format(date_date = str(ap_date), time_time = str(ap_time))
    # mime the text so it meets the Email requirements
    message = email.mime.text.MIMEText(text, 'html')
    message['to'] = patient_email
    message['from'] = "Consultorio Dental"
    message['subject'] = "Recordatorio de Cita"
    # encode the message
    b64_message = base64.urlsafe_b64encode(message.as_bytes())
    # convert the message to string
    to_string = b64_message.decode()
    # return the raw message to the next funciton to send it
    return {'raw': to_string}

# Function that sends the previously formulated message
def send_message(service, user_id, message):
    try:
        service.users().messages().send(userId="me", body=message).execute()
    except requests.HTTPError:
        print("ERROR")