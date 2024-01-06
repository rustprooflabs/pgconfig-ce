"""Parses PostgreSQL config data from pickled files"""
import os
import logging
import pandas as pd
import pickle

from webapp import config

LOGGER = logging.getLogger(__name__)
VERSIONS = ['15', '12']


NEW_STRING = 'Configuration parameter added'
REMOVED_STRING = 'Configuration parameter removed'


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

    # When old is empty, and new is not, it's a new parameters
    if is_NaN(row['default_config_line']) and not is_NaN(row['default_config_line2']):
        changes.append('Configuration parameter added')
        return delim.join(changes)

    # When new is empty and old is not, it was removed
    if is_NaN(row['default_config_line2']) and not is_NaN(row['default_config_line']):
        changes.append('Configuration parameter removed')
        return delim.join(changes)

    if row['boot_val'] != row['boot_val2']:
        changes.append('Changed default value')
    if row['vartype'] != row['vartype2']:
        changes.append('Changed variable type')
    return delim.join(changes)


def config_changes_html(changes: pd.DataFrame) -> dict:
    """Splits `changes` data into new, removed, and changed.

    Parameters
    -------------------
    changes : pd.DataFrame

    Returns
    -------------------
    changes_html : dict
        Dictionary with keys:
            * new
            * removed
            * changed

        Each item holds the string HTML for the table of the data from input
        DataFrame 
    """
    new = changes[changes.summary == NEW_STRING]
    removed = changes[changes.summary == REMOVED_STRING]
    changed = changes[~changes.summary.isin([NEW_STRING, REMOVED_STRING])]

    new_html = _df_to_html(new)
    removed_html = _df_to_html(removed)
    changed_html = _df_to_html(changed)
    return {'new': new_html, 'removed': removed_html, 'changed': changed_html}


def config_changes_stats(changes: dict) -> dict:
    """Provides counts of changes by type (new, removed, updated) to display.

    Parameters
    ---------------------
    changes : dict

    Returns
    ---------------------
    stats : dict
    """
    new = changes[changes.summary == NEW_STRING].count().max()
    removed = changes[changes.summary == REMOVED_STRING].count().max()
    total = changes.count().max()
    updated = total - new - removed
    stats = {'new': new,
             'updated': updated,
             'removed': removed}
    return stats


def _df_to_html(df):
    """Converts DataFrame to HTML table with classes for formatting.

    Parameters
    ---------------
    df : pandas.DataFrame

    Returns
    ---------------
    str
        HTML table for display.
    """
    classes = ['table', 'table-hover']
    html_raw = '<div id="config_table">{src}</div>'
    src = df.to_html(index=False,
                     classes=classes,
                     justify='center',
                     escape=False)
    html = html_raw.format(src=src)
    return html
