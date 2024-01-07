"""Parses PostgreSQL config data from pickled files"""
import os
import logging
import pandas as pd
import pickle

from webapp import config

LOGGER = logging.getLogger(__name__)
VERSIONS = ['11', '12', '13', '14', '15', '16']


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
    data1 = load_config_data(pg_version=vers1)
    data2 = load_config_data(pg_version=vers2)

    data2 = data2.add_suffix('2')

    combined = pd.concat([data1, data2], axis=1)

    combined['summary'] = combined.apply(classify_changes, axis=1)
    combined['change_display'] = combined.apply(calculate_change_display, axis=1)

    # Create combined columns. Passing in 2nd version first displays latest
    # version if there are any differences.
    squash_column_names = ['short_desc2', 'short_desc']
    new_column = 'short_desc'
    combined = squash_columns(data=combined,
                              original_columns=squash_column_names,
                              new_column=new_column)

    squash_column_names = ['frequent_override2', 'frequent_override']
    new_column = 'frequent_override'
    combined = squash_columns(data=combined,
                              original_columns=squash_column_names,
                              new_column=new_column)

    squash_column_names = ['category2', 'category']
    new_column = 'category'
    combined = squash_columns(data=combined,
                              original_columns=squash_column_names,
                              new_column=new_column)

    squash_column_names = ['history_url2', 'history_url']
    new_column = 'history_url'
    combined = squash_columns(data=combined,
                              original_columns=squash_column_names,
                              new_column=new_column)

    # Limit the columns
    columns = ['summary', 'frequent_override',
               'category', 'short_desc',
               'vartype', 'vartype2',
               'boot_val_display', 'boot_val_display2',
               'enumvals', 'enumvals2', 'change_display',
               'history_url'
    ]
    changed = combined[combined['summary'] != ''][columns]

    return changed

def squash_columns(data: pd.DataFrame, original_columns: list, new_column: str):
    """Coalesces the values from DataFrame columns in `original_columns` list
    into the `new_column` name.  Drops `original_columns`, so can reuse one of
    the column names if desired. e.g `short_desc` and `short_desc2` combined
    into the `short_desc` column.

    Note: This is useful for added and removed items, NOT changed items.

    Parameters
    ---------------------
    data : pd.DataFrame
    original_columns : list
    new_column : str

    Returns
    ---------------------
    data_new : pd.DataFrame
    """
    data['tmp'] = data[original_columns].bfill(axis=1).iloc[:, 0]
    data_mid = data.drop(columns=original_columns)
    data_new = data_mid.rename(columns={'tmp': new_column})
    return data_new


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
    # Checking user input against configured versions to avoid security concerns
    if str(pg_version) not in VERSIONS:
        raise ValueError(f'Invalid Postgres version.  Options are {VERSIONS}')

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

    # Add hyperlink to the parameter history page
    html_part1 = '<a href="/param/'
    html_part2 = '" target="blank"><i class="fa fa-external-link" aria-hidden="true"></i></a>'
    df['history_url'] = html_part1 + df['name'] + html_part2

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


def calculate_change_display(row: pd.Series) -> str:
    """Used by dataFrame.apply on the combined DataFrame to create the columns
    to display for changes.

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

    # If either is Nan, don't calculate
    if is_NaN(row['default_config_line']) or is_NaN(row['default_config_line2']):
        return None

    if row.boot_val != row.boot_val2:
        changes.append(f'Default value: {row.boot_val} -> {row.boot_val2}')
    if row['vartype'] != row['vartype2']:
        changes.append(f'Variable type: <code>{row.vartype}</code> -> <code>{row.vartype2}</code>')
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
    # New Section
    columns_new = ['category', 'short_desc', 'boot_val_display2',
                   'vartype2', 'enumvals2', 'history_url']
    rename_columns_new = {'vartype2': 'Var Type',
                          'boot_val_display2': 'Default Value',
                          'enumvals2': 'Enum Values'
                          }
    new = changes[changes.summary == NEW_STRING][columns_new].rename(columns=rename_columns_new)

    new_html = _df_to_html(new)

    # Removed Section
    columns_removed = ['category', 'short_desc', 'boot_val_display',
                       'vartype', 'enumvals', 'history_url']
    rename_columns_removed = {'vartype': 'Var Type',
                          'boot_val_display': 'Default Value',
                          'enumvals': 'Enum Values'
                          }
    removed = changes[changes.summary == REMOVED_STRING][columns_removed].rename(columns=rename_columns_removed)
    removed_html = _df_to_html(removed)

    # Changed section
    columns_changed = ['category', 'short_desc', 'change_display',
                       'history_url']
    rename_columns_changed = {'vartype': 'Var Type',
                          'change_display': 'Changed:',
                          'enumvals': 'Enum Values'
                          }
    changed = changes[~changes.summary.isin([NEW_STRING, REMOVED_STRING])][columns_changed].rename(columns=rename_columns_changed)
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
    default_renames = {'category': 'Category', 'short_desc': 'Description'}
    df.rename(columns=default_renames, inplace=True)
    src = df.to_html(index=True,
                     classes=classes,
                     justify='center',
                     escape=False)
    html = html_raw.format(src=src)
    return html
