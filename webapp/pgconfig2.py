"""Parses PostgreSQL config data from pickled files"""
import os
import logging
import pandas as pd
import pickle

from webapp import config

LOGGER = logging.getLogger(__name__)
VERSIONS = ['15', '12']


def config_changes(vers1: int, vers2: int) -> pd.DataFrame:
    """Find changes between `vers1` and `vers2`.

    Parameters
    ----------------
    vers1 : int
        Version number, e.g. 11 or 16

    vers2 : int
        Version number, e.g. 11 or 16

    Returns
    -----------------
    changed : pd.DataFrame
    """
    if vers2 <= vers1:
        raise ValueError('Version 1 must be lower (before) version 2.')

    # Have to drop enumvals in comparison to avoid errors comparing using pandas
    data1 = load_config_data(pg_version=vers1).drop(columns='enumvals')
    data2 = load_config_data(pg_version=vers2).drop(columns='enumvals')

    data2 = data2.add_suffix('2')

    combined = pd.concat([data1, data2], axis=1)

    combined['summary'] = combined.apply(classify_changes, axis=1)
    columns = ['summary', 'vartype', 'vartype2',
            'boot_val_display', 'boot_val_display2']
    changed = combined[combined['summary'] != ''][columns]

    return changed


def load_config_data(pg_version: int) -> pd.DataFrame:
    """Loads the pickled config data for `pg_version` into DataFrame with the
    config name as the index.

    Returns empty DataFrame on file read error.

    Parameters
    ----------------------
    pg_version : int

    Returns
    ----------------------
    df : pd.DataFrame
    """ 
    base_path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.join(base_path, 'config', f'pg{pg_version}.pkl')

    try:
        with open(filename, 'rb') as data_file:
            config_data = pickle.load(data_file)

        df = pd.DataFrame(config_data)
    except FileNotFoundError:
        msg = f'File not found for Postgres version {pg_version}'
        print(msg)
        LOGGER.error(msg)
        df = pd.DataFrame()
        return df

    df.set_index('name', inplace=True)
    return df

def is_NaN(input: str) -> bool:
    """Checks string values for NaN, aka it isn't equal to itself.

    Parameters
    ------------------------
    input : str

    Returns
    ------------------------
    is_nan : bool
    """
    return input != input


def classify_changes(row: pd.Series) -> str:
    """Used by dataFrame.apply on the combined DataFrame to check version1 and
    version2 values, types, etc. for differences.

    Parameters
    --------------------------
    row : pd.Series
        Row from combined DataFrame to check details.

    Returns
    -------------------------
    changes : str
        Changes are built as a list internally and returned as a string
        with a comma separated list of changes.
    """
    changes = []
    delim = ', '

    if is_NaN(row['default_config_line']) and not is_NaN(row['default_config_line2']):
        changes.append(f'Configuration parameter added')
        return delim.join(changes)

    if is_NaN(row['default_config_line2']) and not is_NaN(row['default_config_line']):
        changes.append(f'Configuration parameter removed')
        return delim.join(changes)

    if row['boot_val'] != row['boot_val2']:
        changes.append('Changed default value')
    if row['vartype'] != row['vartype2']:
        changes.append('Changed variable type')
    return delim.join(changes)

