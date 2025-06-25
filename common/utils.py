from datetime import datetime
import io
from django.apps import apps
from django.conf import settings
from django.http import HttpResponse
from pytz import UTC
from re import compile, sub
from sys import argv as sys_argv
import qrcode

from jwt import decode
from logging import getLogger

import pandas as pd
import json
logger = getLogger(__name__)

# DATES FUNCTIONS
def datetime_now():

    return datetime.now(tz=UTC)


# STRING FUNCTIONS
to_title_pattern = compile('.[^A-Z0-9._-]*')
def to_title(name, capitalize=True):
    title = ''.join(to_title_pattern.findall(name))
    title = title.replace('_', '').replace('-', '').replace('.', '')
    title = title.replace(' ', '') 
    if capitalize:
        return title.title()
    return title

def to_mapping_key(txt_string, replace_spaces_with='_'):

    return sub(f'{replace_spaces_with}+', replace_spaces_with, \
        sub(f'[^a-z0-9{replace_spaces_with}]+', '', \
        sub('[._ -]+', replace_spaces_with, txt_string.lower()))
    )[:100]


# FORMAT CHECKERS
mapping_key_format = compile('^[a-z0-9_-]+$')
def is_valid_mapping_key(mapping_key_string):
    invalid_mapping_keys = []
    return isinstance(mapping_key_string, str) \
        and mapping_key_format.match(mapping_key_string) \
        and mapping_key_string not in invalid_mapping_keys


# COMMAND CHECKERS
def server_is_running():
    """ Checks if the server is running and not executing commands as migrate or loaddata """

    return 'runserver' in sys_argv

def is_running_commands():
    """ Checks if is executing 'migrate', 'loaddata' or 'create_admin' commands """

    return 'migrate' in sys_argv or 'loaddata' in sys_argv or 'create_admin' in sys_argv

# URL PARAMETERS
# - TOKENS
regex_for_token = r'(?P<token>[A-z0-9_-]{86})'

# - UUID
def regex_for_uuid_of(param=None):

   return '(?P<%suuid>[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12})' % ((param + '_') if param else '')

regex_for_uuid = regex_for_uuid_of()

regex_for_optional_uuid = '(/%s)?/?$' % (regex_for_uuid)

# QR GENERATOR
def generateQr(token,scopes):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    # Decode token
    try:
        token_claims = decode(
            token,
            settings.JWT_SECRET,
            algorithms=['HS256'],
            **({'audience': scopes.origin} if settings.JWT_AUD_CHECK else {})
        )
    except Exception as err:
        try: logger.warning('Invalid Token: %s -> %s' % (err, decode(token, options={'verify_signature': False})))
        except: logger.warning('Invalid Token: %s' % (err))
        return None
    # Account
    if token_claims['type'] == 'user':
        # Get Account
        account = apps.get_model('users.Account').objects.select_related('user').filter(
            user_id=token_claims['sub'],
            user__email=token_claims['email'],
            is_active=True,
        ).first()
    if not account:
        return HttpResponse(status=404)
    
    data = settings.API_URL + '/auth/v1/login_rq/?token='+token

    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # STATIC MODE
    # Save the image file in memory
    # buffer = BytesIO()
    # img.save(buffer)
    # buffer.seek(0)

    # # Saving the file to the file system using Django Storage

    # timestamp = int(datetime_now().timestamp() * 1000)
    # file_path = 'user/%s/qr/%s.png' % (scopes.account.user.uuid, timestamp)
    
    # default_storage.save(file_path, ContentFile(buffer.getvalue()))
    # return  file_path
    # Create a byte stream object to store the image

    # DINAMIC MODE
    byte_stream = io.BytesIO()
    img.save(byte_stream, format='PNG')
    byte_stream.seek(0)

    return byte_stream


class ExcelCSVProcessor:
    def __init__(self, file_path, file_type='csv'):
        self.file_path = file_path
        self.file_type = file_type.lower()
        self.data = self._read_file()

    def _read_file(self):
        if self.file_type == 'csv':
            data = pd.read_csv(self.file_path)
        elif self.file_type in ['xls', 'xlsx']:
            data = pd.read_excel(self.file_path)
        else:
            raise ValueError("Unsupported file type. Use 'csv', 'xls', or 'xlsx'.")
        
        data.columns = [col.lower() for col in data.columns]
        print(f"Data columns after reading file: {data.columns}")  # Debugging line
        return data

    def process_columns(self, columns):
        
        try:
            columns = json.loads(columns)
            if columns:
                columns = [col.strip().lower() for col in columns]
            else:
                raise ValueError("No columns specified")
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON payload")
        
        if not all(column in self.data.columns for column in columns):
            missing_columns = [column for column in columns if column not in self.data.columns]
            raise ValueError(f"Some columns are not in the data: {missing_columns}")
        self.data = self.data[columns]

    def to_json(self):
        return self.data.to_json(orient='records')
