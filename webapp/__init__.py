import logging
from flask import Flask
from webapp import config

# App settings
app = Flask(__name__)
app.config['DEBUG'] = config.APP_DEBUG
app.config['SECRET_KEY'] = config.APP_SECRET_KEY
app.config['WTF_CSRF_ENABLED'] = True

# Setup Logging
LOG_PATH = config.LOG_PATH
LOGGER = logging.getLogger(__name__)
HANDLER = logging.FileHandler(filename=LOG_PATH, mode='a+')
FORMATTER = logging.Formatter(config.LOG_FORMAT)
HANDLER.setFormatter(FORMATTER)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(logging.DEBUG)

from webapp import routes
