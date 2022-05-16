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

import google_auth_oauthlib
from sender import email_sequence
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
CLIENT_SECRET_FILE = "credentials_calendar.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
API_SERVICE_NAME = 'calendar'
API_VERSION = 'v2'


def main(creds_calendar, creds_gmail):
    service = build('calendar', 'v3', credentials=creds_calendar)
    
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
            email_sequence(email[0], event['start']['dateTime'][11:16], event['start']['dateTime'][0:10], creds_gmail)

if __name__ == '__main__':
    main()