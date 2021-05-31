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

# Original file obtained from: https://github.com/googleworkspace/python-samples/blob/master/calendar/quickstart/quickstart.py
# Used to make the connection with the API
# Modified to achieve what was needed in the current application

from __future__ import print_function
import datetime
import os.path
import re
from sender import email_sequence
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token-calendar.json'):
        creds = Credentials.from_authorized_user_file('token-calendar.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials_calendar.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token-calendar.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    
    # Gets tomorrow's date to send it to the API
    tmr = datetime.datetime.today() + datetime.timedelta(days=1)
    # Gets date 2 days from now to send it to the API
    tmr_tmr = datetime.datetime.today() + datetime.timedelta(days=2)
    # Format the minimum time to meet the API's requirements
    tmin = tmr.strftime("%Y-%m-%dT00:00:00Z")
    # Format the maximum time to meet the API's requirements
    tmax = tmr_tmr.strftime("%Y-%m-%dT05:00:00Z")
    # Send the data to the calendar to retrieve the events
    events_result = service.events().list(calendarId='primary', timeMin=tmin, timeMax=tmax, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        # Using regex, the email is found within all of the event's description
        email = re.findall(r'[\w\.-]+@[\w\.-]+', event['description'])
        # if an email is found in the appoitment, the email is sent, otherwise it is ignored
        if len(email) > 0:
            # Send an email sequence per each event found in the calendar
            email_sequence(email[0], event['start']['dateTime'][11:16], event['start']['dateTime'][0:10])

if __name__ == '__main__':
    main()