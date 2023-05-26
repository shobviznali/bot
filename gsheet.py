from __future__ import print_function
import os.path
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GoogleSheet:
    SPREADSHEET_ID = '1KEzZcQyyj70n47TtkH9DVfqp-WuTqn6LNtJjKczhFXk'
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    service = None

    def __init__(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'creds.json', self.SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('sheets', 'v4', credentials=creds)

    def get_column_index(self, identifier):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range='Sheet1!B1:B1').execute()
        headers = result.get('values', [])
        if headers:
            headers_row = headers[0]
            for i, header in enumerate(headers_row):
                if header == identifier:
                    return i + 2  # Adding 2 to match the column index

        return 1

    def add_column(self, identifier):
        sheet = self.service.spreadsheets()
        request = {
            'insertDimension': {
                'range': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 2,
                    'endIndex': 3
                },
                'inheritFromBefore': False
            }
        }

        response = sheet.batchUpdate(
            spreadsheetId=self.SPREADSHEET_ID,
            body={'requests': [request]}
        ).execute()

        values = [[identifier]]
        range_str = f'Sheet1!{self._get_column_letter(2)}2'
        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': range_str,
                    'values': values
                }
            ]
        }

        sheet.values().batchUpdate(spreadsheetId=self.SPREADSHEET_ID, body=body).execute()


    def get_last_row(self):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range='Sheet1!A:A').execute()
        values = result.get('values', [])
        return len(values) + 1

    def find_user_and_get_text(self, name):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range='Sheet1!A1:ZZ').execute()
        values = result.get('values', [])

        for row in values:
            if row and row[0] == name:
                return row[1:]

        return []

    def update_glider(self, identifier, date):
        column_index = self.get_column_index(identifier)
        if column_index is None:
            return False

        sheet = self.service.spreadsheets()
        last_row = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range='Sheet1!A:A').execute().get('values')
        next_row = len(last_row) + 1 if last_row else 2

        glider_values = [[f'{identifier}']]
        if next_row % 2 == 0:
            pass

        range_str = f'Sheet1!{self._get_column_letter(column_index)}{next_row}:B{next_row + 1}'

        print('Updating glider...')
        print('Range:', range_str)
        print('Values:', glider_values)

        body = {
            'valueInputOption': 'USER_ENTERED',
            'data': [
                {
                    'range': range_str,
                    'values': glider_values
                }
            ]
        }

        result = sheet.values().batchUpdate(spreadsheetId=self.SPREADSHEET_ID, body=body).execute()
        print('Result:', result)

        return True

    def update_text_for_user(self, name, text):
        sheet = self.service.spreadsheets()
        result = sheet.values().get(spreadsheetId=self.SPREADSHEET_ID, range='Sheet1!A1:ZZ').execute()
        values = result.get('values', [])

        for row_index, row in enumerate(values):
            if row and row[0] == name:
                for col_index, cell in enumerate(row[1:], start=1):
                    if not cell:
                        col_letter = self._get_column_letter(col_index + 1)
                        cell_range = f'Sheet1!{col_letter}{row_index + 1}'
                        body = {
                            'values': [[text]],
                        }

                        result = sheet.values().update(
                            spreadsheetId=self.SPREADSHEET_ID,
                            range=cell_range,
                            valueInputOption='USER_ENTERED',
                            body=body
                        ).execute()
                        return True

                # If no empty cell found, add a new column and update the text there
                col_index = len(row) + 1
                col_letter = self._get_column_letter(col_index)
                cell_range = f'Sheet1!{col_letter}{row_index + 1}'
                body = {
                    'values': [[text]],
                }

                result = sheet.values().update(
                    spreadsheetId=self.SPREADSHEET_ID,
                    range=cell_range,
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                return True

        return False

    @staticmethod
    def _get_column_letter(column_index):
        div = column_index
        column_letter = ''
        while div:
            (div, mod) = divmod(div - 1, 26)
            column_letter = chr(mod + 65) + column_letter

        return column_letter
