# -*- coding: UTF-8 -*-
import os

CUR_DIR = os.path.dirname(os.path.realpath(__file__))

USERS = { # Override this in `settings_local.py`
  # UserName as key
  'guest':{
    'password': 'guest',
    # type role = Enum(guest|vip|mandator|admin)
    #   guest: only have the permission to `fetch` public rank domains
    #   vip: have the permission to `fetch` all rank domains
    #   mandator: can `fetch` and `update` all domains
    #   admin: reserved
    'role': 'guest'
  }
}

# Enum(''|'production')
environment = ''

host = '127.0.0.1'
port = 1988

# Set the CA file path to enable https
ssl_certificate = ''
ssl_private_key = ''

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),'db.sqlite3')


RANK_ZERO_APPEND_FILE = CUR_DIR+'/rank-zero.txt'

from settings_local import *
