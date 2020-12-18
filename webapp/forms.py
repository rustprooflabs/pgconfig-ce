"""Provides Flask Forms related functionality."""
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm

PG_EXAMPLE = """For example:

# -----------------------------
# PostgreSQL configuration file
# -----------------------------

#------------------------------------------------------------------------------
# CONNECTIONS AND AUTHENTICATION
#------------------------------------------------------------------------------

# - Connection Settings -

listen_address = '*'
#listen_addresses = 'localhost'         # what IP address(es) to listen on;
                                        # comma-separated list of addresses;
                                        # defaults to 'localhost'; use '*' for all
                                        # (change requires restart)
#port = 5432                            # (change requires restart)
"""

class PostgresConfigForm(FlaskForm):
    """ Form object to provide ability to compare custom postgresql.conf files
    """
    config_raw = TextAreaField('Paste your postgresql.conf contents here *',
                         validators=[DataRequired()],
                         render_kw={"placeholder": PG_EXAMPLE,
                         			"rows": 20})
