import base64
import os
import re
# import time - if you want to slow down the run

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# If modifying these SCOPES, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify', 'https://www.googleapis.com/auth/gmail.send']

COUNTER = 2


def get_service():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('my_token.json'):
        creds = Credentials.from_authorized_user_file('my_token.json')

    # If there are no (valid) credentials available, prompt the user to log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'leahgolub1.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('my_token.json', 'w') as token:
                token.write(creds.to_json())

    # Call the Gmail API
    service = build('gmail', 'v1', credentials=creds)
    return service


def check_for_send_email(service):
    results = service.users().messages().list(userId='me', q="is:unread subject:Oh no! An infinite loop!").execute()
    while results:
        messages = results.get('messages', [])

        if not messages:
            print('No new "Oh no! An infinite loop!" emails found.')
            break
        else:
            # If there are more than one unread emails, mark the one before the last as read
            if len(messages) > 1:
                penultimate_msg_id = messages[-1]['id']
                service.users().messages().modify(userId='me', id=penultimate_msg_id,
                                                  body={'removeLabelIds': ['UNREAD']}).execute()
                print(f'Marked email with ID {penultimate_msg_id} as read.')
            Fibonacci_directly_to_email(service, messages)

        results = service.users().messages().list(userId='me', q="is:unread subject:Oh no! An infinite loop!").execute()


def Fibonacci_directly_to_email(service, messages):
    global COUNTER
    list_of_found = []
    list_of_email_number_found = []
    from_email = ""
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        email_text = msg['snippet']
        match = re.search(r'Fibonacci value is: (\d+)', email_text)
        match2 = re.search(r'Email number (\d+)', email_text)
        if not match or not match2:
            email_text = msg["payload"]["body"]["data"]
            decoded_bytes = base64.urlsafe_b64decode(email_text)
            decoded_string = decoded_bytes.decode('utf-8')
            match = re.search(r'Fibonacci value is: (\d+)', decoded_string)
            match2 = re.search(r'Email number (\d+)', decoded_string)

        if match:
            email_fib_number = int(match.group(1))
            list_of_found.append(email_fib_number)
        else:
            print('Fibonacci number not found in email content.')
            exit(1)

        if match2:
            email_number = int(match2.group(1))
            list_of_email_number_found.append(email_number)
        else:
            print('Email number not found in email content.')
            exit(1)

        email_data = msg['payload']['headers']
        for value in email_data:
            name = value['name']
            if name == 'From':
                from_email = value['value']
                break

    fib_sum = list_of_found[0] + list_of_found[1]
    # Create the email body
    email_text = """\
From: Your Email Address
To: {}
Subject: Fibonacci {} Oh no! An infinite loop!

Stop! Break! Help! Email number {}. Triggered from email number {} and {}. The Fibonacci value is: {}.\nIn other words, 
the formula is: a{} = a{} + a{} ===> a{} = {} + {} = {}.
""".format(from_email, fib_sum, COUNTER, list_of_email_number_found[0], list_of_email_number_found[1], fib_sum,
            COUNTER, list_of_email_number_found[0], list_of_email_number_found[1], COUNTER, list_of_found[0],
            list_of_found[1], fib_sum)
    COUNTER += 1

    message = base64.urlsafe_b64encode(email_text.encode('utf-8')).decode('utf-8')

    body = {'raw': message}
    service.users().messages().send(userId='me', body=body).execute()
    print('Sent response to:', from_email)


def delete_emails_with_subject(service, subject):
    """Delete all emails with the specified subject."""
    query = f'subject:"{subject}"'
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])

    for message in messages:
        service.users().messages().delete(userId='me', id=message['id']).execute()
        print(f'Deleted email with ID: {message["id"]}')


if __name__ == '__main__':
    # Send 2 emails to initialize manually, or alternatively - add a simple function to do so
    service = get_service()
    check_for_send_email(service)
