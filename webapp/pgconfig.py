"""Parses PostgreSQL config files"""
import os
import pandas as pd
import numpy as np
import logging
from webapp import config

LOGGER = logging.getLogger(__name__)
VERSIONS = ['16beta1', '15', '14', '13', '12', '11', '10', '9.6', '9.5',
            '9.4', '9.3', '9.2']

VERSION_REDIRECTS = [{'version': '12beta4', 'redirect': '12'}]

def get_all_config():
    """
    Returns
    -------------
    pandas.DataFrame
    """
    config_all = dict()

    for version in VERSIONS:
        try:
            # Ingoring dups list in second part out output
            version_conf, _ = parse_pg_config(version=version)
        except FileNotFoundError:
            version_conf = False

        config_all[version] = version_conf

    config_summary = build_config_summary(config_all)
    return config_summary

def compare_custom_config(vers1, config_raw):
    """Compares user-uploaded `config_raw` to default config for `vers1`

    Parameters
    --------------
    vers1 : str
        Version number in str format.  e.g. 11 or 9_6

    config_raw : str
        Raw uploaded postgresql.conf from user form.

    Returns
    --------------
    config_summary : pandas.DataFrame

    dups : list
        List of duplicates found in custom configuration
    """
    if not vers1 in VERSIONS:
        raise ValueError(f'Version {vers1} not available')

    config_all = dict()
    custom_config, dups = parse_pg_config(version='custom',
                                          custom_config=config_raw)
    LOGGER.debug('Custom config: %s', custom_config)
    LOGGER.debug('Custom config has dups?  : %s', len(dups))
    config_all['custom'] = custom_config

    version_conf, _ = parse_pg_config(version=vers1)
    config_all[vers1] = version_conf

    config_summary = build_config_summary(config_all)
    return config_summary, dups


def config_to_html(config_summary,
                   filter_value='max_parallel_workers_per_gather'):
    """Converts `config_summary` to HTML table.  Filters for `filter_value`.

    Parameters
    --------------------
    config_summary : pandas.DataFrame

    filter_value : str
        (Optional) value to filter for.  Has default set.

    Returns
    --------------------
    html : str
        HTML for data table to display
    """
    data = config_summary[config_summary['parameter'] == filter_value]
    html = _df_to_html(data)
    return html

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

def config_changes(config_summary, vers1, vers2):
    """Uses `config_summary` to find changes between `vers1` and `vers2`.

    Parameters
    ----------------
    config_summary : pandas.DataFrame
        Full data set with all loaded versions.

    vers1 : str
        Version number in str format.  e.g. 11 or 9_6

    vers2 : str
        Version number in str format.  e.g. 11 or 9_6

    Returns
    ----------------
    changes : pandas.DataFrame
        Subset of data from `config_summary` for `vers1` and `vers2`.
    """
    try:
        data = config_summary[['parameter', vers1, vers2]]
    except KeyError as err:
        LOGGER.error('Config version not found. %s', err)
        raise
    changes = data[(data[vers1] != data[vers2])
                   & (data[vers1].notnull() | data[vers2].notnull())]
    return changes

def config_changes_html(changes):
    """Converts `changes` DataFrame into HTML table.

    Additionally, creates column with URL to parameter's history over versions
    of Postgres.

    Parameters
    ---------------
    changes : pandas.DataFrame

    Returns
    ---------------
    html : str
        HTML table for display.
    """
    # Add `history` column with URL to param history (if exists)
    html_part1 = '<a href="/param/'
    html_part2 = '" target="blank"><i class="fa fa-external-link" aria-hidden="true"></i></a>'
    changes['history'] = html_part1 + changes['parameter'] + html_part2

    html = _df_to_html(changes)
    return html

def config_changes_stats(changes, vers1, vers2):
    """Generates basic statistics for changes between two versions.

    Parameters
    ---------------
    changes : pandas.DataFrame

    vers1 : str

    vers2 : str

    Returns
    ---------------
    change_stats : dict
    """
    change_stats = dict()
    new = changes[changes[vers1].isna()].count().max()
    removed = changes[changes[vers2].isna()].count().max()
    updatedtmp = changes[(changes[vers1] != changes[vers2])].dropna()
    updated = updatedtmp.count().max()
    change_stats['new'] = new
    change_stats['updated'] = updated
    change_stats['removed'] = removed
    return change_stats



def custom_config_changes_stats(changes, vers1):
    """Generates basic statistics for changes between two versions.

    Parameters
    ---------------
    changes : pandas.DataFrame

    vers1 : str

    Returns
    ---------------
    change_stats : dict
        Data for display.

        Keys:
            * invalid_param_custom
            * default_setting
            * updated
            * duplicates : dict
    """
    change_stats = dict()
    vers2 = 'custom'

    # Assuming vers1 has ALL options, no new items should be in custom
    invalid_param_custom = changes[changes[vers1].isna()].count().max()
    default_setting = changes[changes[vers2].isna()].count().max()

    updatedtmp = custom_config_updated_params(changes, vers1)
    updated = updatedtmp.count().max()

    change_stats['invalid_param_custom'] = invalid_param_custom
    change_stats['default_setting'] = default_setting
    change_stats['updated'] = updated
    return change_stats

def custom_config_invalid_params(changes, vers1):
    """Generates data frame of invalid parameters in custom configuration.

    Parameters
    ---------------
    changes : pandas.DataFrame

    vers1 : str

    Returns
    ---------------
    pandas.DataFrame
    """
    invalid_param_custom = changes[changes[vers1].isna()]
    return invalid_param_custom

def custom_config_updated_params(changes, vers1):
    """Generates data frame of updated parameters in custom configuration.

    Updated parameters have changed from the base default version.

    Parameters
    ---------------
    changes : pandas.DataFrame

    vers1 : str

    Returns
    ---------------
    pandas.DataFrame
    """
    vers2 = 'custom'
    return changes[(changes[vers1] != changes[vers2])].dropna()


def parse_pg_config(version='13', custom_config=None):
    """Parses PostgreSQL configuration (postgresql.conf).

    Parameters
    ----------------
    version : str
        Version number in str format.  e.g. 11 or 9_6

    custom_config : str
        If value provided, does NOT load from file, insteads parses this content.
        default = `None`

    Returns
    ----------------
    df : pandas.DataFrame
        Configurations from parsed file.

    dups : list
        List of duplicated keys with all defined values.
    """
    lines = _get_config_lines(version, custom_config)
    pg_config_options, dups = _parse_config_lines(lines)

    columns = ['parameter', version]
    LOGGER.debug('Parameters loaded: %s', len(pg_config_options))
    df = pd.DataFrame(pg_config_options, columns=columns)
    return df, dups


def _get_config_lines(version, custom_config):
    """Returns PostgreSQL configuration (postgresql.conf) lines.

    Removes comments from configuration.

    Parameters
    ----------------
    version : str
        Version number in str format.  e.g. 11 or 9_6

    custom_config : str
        If value provided, does NOT load from file, insteads parses this content.
        default = `None`

    Returns
    ----------------
    lines : list
        Lines from config with key = value pairs.
    """
    lines = list()
    if custom_config is None:
        # Load from file based on version
        filepath = _pg_config_filepath(version)
        with open(filepath) as config_file:
            for line_raw in config_file:
                line = _parse_line_remove_comment(line_raw)
                if line == '':
                    continue
                lines.append(line)
    else:
        # Load from `custom_config`
        for line_raw in custom_config.splitlines():
            line = _parse_line_remove_comment(line_raw)
            if line == '':
                continue
            lines.append(line)

    return lines

def _parse_config_lines(lines):
    """Parses out lines from Postgres configuration.

    Detects (and keeps) duplicates in full list and returns second list
    with details about duplicates.

    Parameters
    ------------------
    lines : list
        Results from `_get_config_lines()`

    Returns
    ------------------
    pg_config_options : list
        List of all options found defined in the configuration.
        Includes keys defined multiple times.

    dups : list
        List of keys defined multiple times in configuration.
        A non-empty list indicates an error in the configuration!
    """
    pg_config_options = list()
    keys = set() # Tracks keys already parsed
    dup_keys = set() # Tracks duplicate keys found

    for line in lines:
        key, value = line.partition("=")[::2]
        key = key.strip()
        value = value.strip()

        # If Key already found, mark as duplicate key
        if key in keys:
            dup_keys.add(key)

        keys.add(key)
        pg_config_options.append([key, value])

    dups = list()
    for key in dup_keys:
        LOGGER.debug(f'Finding configs for {key}')
        for row in pg_config_options:
            if row[0] == key:
                dups.append(row)

    return pg_config_options, dups


def _pg_config_filepath(version):
    """Gets filepath for version-specific config.

    Parameters
    ---------------
    version : str
        Version number in str format.  e.g. 11 or 9_6

    Returns
    ---------------
    filepath : str
        Full path to the config file for specific version
    """
    config_path = os.path.join(config.CURR_PATH, 'config')
    filename = f'postgresql-{version}.conf'
    filepath = os.path.join(config_path, filename)
    LOGGER.debug('Loading config: %s', filepath)
    return filepath

def _parse_line_remove_comment(line):
    """Parses line from config, removes comments and trailing spaces.

    Lines starting with "#" are skipped entirely.  Lines with comments after
    the parameter retain their parameter.

    Parameters
    --------------
    line : str

    Returns
    --------------
    line : str
    """
    i = line.find('#')
    if i >= 0:
        line = line[:i]
    return line.strip()


def build_config_summary(config_all):
    """Collect all configuration parameters from all configurations.

    Parameters
    ------------
    config_all : dict
        Dict of pandas.DataFrames with Pg version as key.

    Returns
    ------------
    df : pandas.DataFrame
    """
    LOGGER.debug('Building config summary data')
    df = config_all.popitem()[1]
    while config_all:
        key, df_new = config_all.popitem()
        LOGGER.debug('Summary key:  %s', key)
        if isinstance(df_new, pd.DataFrame):
            df = pd.merge(df, df_new, how='outer', on='parameter')
        else:
            df[key] = np.nan

    return df


def check_redirect(version):
    """Checks version for defined redirects.

    e.g. 12beta4 redirects to 12 once the production-ready version
    is released.

    Parameters
    ---------------
    version : str
        Version to check for redirects for.

    Returns
    ---------------
    version : str
        Redirected if necessary, original version if not.
    """
    for redirect in VERSION_REDIRECTS:
        if version == redirect['version']:
            LOGGER.info('Redirecting version %s to %s', version,
                                                        redirect['redirect'])
            return redirect['redirect']
    return version
