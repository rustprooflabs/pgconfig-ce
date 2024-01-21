"""Database helper module.
Modified from https://gist.github.com/rustprooflabs/3b8564a8e7b7fe611436b30a95b7cd17,
adapted to psycopg 3 from psycopg2.
"""
import getpass
import psycopg


def prepare():
    """Ensures latest `pgconfig.settings` view exists in DB to generate config.
    """
    print('Preparing database objects...')
    ensure_schema_exists()
    ensure_view_exists()
    print('Database objects ready.')


def ensure_schema_exists():
    """Ensures the `pgconfig` schema exists."""
    sql_raw = 'CREATE SCHEMA IF NOT EXISTS pgconfig;'
    _execute_query(sql_raw, params=None, qry_type='ddl')


def ensure_view_exists():
    """Ensures the view `pgconfig.settings` exists."""
    sql_file = 'create_pgconfig_settings_view.sql'
    with open(sql_file) as f:
        sql_raw = f.read()

    _execute_query(sql_raw, params=None, qry_type='ddl')


def select_one(sql_raw: str, params: dict) -> dict:
    """ Runs SELECT query that will return zero or 1 rows.
    
    Parameters
    -----------------
    sql_raw : str
    params : dict
        Params is required, can be `None` if query returns a single row
        such as `SELECT version();`

    Returns
    -----------------
    data : dict
    """
    return _execute_query(sql_raw, params, 'sel_single')


def select_multi(sql_raw, params=None) -> list:
    """ Runs SELECT query that will return multiple.  `params` is optional.

    Parameters
    -----------------
    sql_raw : str
    params : dict
        Params is optional, defaults to `None`.

    Returns
    ------------------
    data : list
        List of dictionaries.
    """
    return _execute_query(sql_raw, params, 'sel_multi')


def get_db_string() -> str:
    """Prompts user for details to create connection string

    Returns
    ------------------------
    database_string : str
    """
    db_host = input('Database host [127.0.0.1]: ') or '127.0.0.1'
    db_port = input('Database port [5432]: ') or '5432'
    db_name = input('Database name: ')
    db_user = input('Enter PgSQL username: ')
    db_pw = getpass.getpass('Enter password (empty for pgpass): ') or None

    if db_pw is None:
        database_string = 'postgresql://{user}@{host}:{port}/{dbname}'
    else:
        database_string = 'postgresql://{user}:{pw}@{host}:{port}/{dbname}'

    return database_string.format(user=db_user, pw=db_pw, host=db_host,
                                  port=db_port, dbname=db_name)

DB_STRING = get_db_string()

def get_db_conn():
    """Uses DB_STRING to establish psycopg connection."""
    db_string = DB_STRING

    try:
        conn = psycopg.connect(db_string)
    except psycopg.OperationalError as err:
        err_msg = f'DB Connection Error - Error: {err}'
        print(err_msg)
        return False

    return conn


def _execute_query(sql_raw, params, qry_type):
    """ Handles executing all types of queries based on the `qry_type` passed in.
    Returns False if there are errors during connection or execution.
        if results == False:
            print('Database error')
        else:
            print(results)
    You cannot use `if not results:` b/c 0 results is a false negative.
    """
    try:
        conn = get_db_conn()
    except psycopg.ProgrammingError as err:
        print(f'Connection not configured properly.  Err: {err}')
        return False

    if not conn:
        return False

    cur = conn.cursor(row_factory=psycopg.rows.dict_row)

    try:
        cur.execute(sql_raw, params)
        if qry_type == 'sel_single':
            results = cur.fetchone()
        elif qry_type == 'sel_multi':
            results = cur.fetchall()
        elif qry_type == 'ddl':
            conn.commit()
            results = True
        else:
            raise Exception('Invalid query type defined.')

    except psycopg.BINARYProgrammingError as err:
        print('Database error via psycopg.  %s', err)
        results = False
    except psycopg.IntegrityError as err:
        print('PostgreSQL integrity error via psycopg.  %s', err)
        results = False
    finally:
        conn.close()

    return results
