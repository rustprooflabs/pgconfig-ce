"""Config module for PgConfig webapp."""
import os
import logging

CURR_PATH = os.path.abspath(os.path.dirname(__file__))
PROJECT_BASE_PATH = os.path.abspath(os.path.join(CURR_PATH, os.pardir))

APP_NAME = 'PG Configuration Tracking'

LOG_FORMAT = '%(levelname)s - %(asctime)s - %(name)s - %(message)s'

LOGGER = logging.getLogger(__name__)

try:
    LOG_PATH = os.environ['LOG_PATH']
except KeyError:
    LOG_PATH = PROJECT_BASE_PATH + '/pgconfig_app.log'

try:
    APP_DEBUG = os.environ['APP_DEBUG']
except KeyError:
    APP_DEBUG = True


# Required for CSRF protection in Flask, please change to something secret!
try:
    APP_SECRET_KEY = os.environ['APP_SECRET_KEY']
except KeyError:
    ERR_MSG = '\nSECURITY WARNING: To ensure security please set the APP_SECRET_KEY'
    ERR_MSG += ' environment variable.\n'
    LOGGER.warning(ERR_MSG)
    print(ERR_MSG)
    APP_SECRET_KEY = 'YourApplicationShouldBeServedFreshWithASecureAndSecretKey!'


SESSION_COOKIE_SECURE = True
REMEMBER_COOKIE_SECURE = True
