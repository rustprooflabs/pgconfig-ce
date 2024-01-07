"""Generates config based on pgconfig.settings and pickles for reuse in webapp.

This code is expected to be used on Postgres 10 and newer.
"""
import pickle
import db


def run():
    """Saves pickled config data from defined database connection.
    """
    db.prepare()
    pg_version_num = get_pg_version_num()
    pg_config_data = get_config_data()
    save_config_data(data=pg_config_data, pg_version_num=pg_version_num)


def get_pg_version_num() -> int:
    """Returns the Postgres version number as an integer.

    Expected to be used on Postgres 10 and newer only.

    Returns
    ------------------------
    pg_version_num : int
    """
    sql_raw = """SELECT current_setting('server_version_num')::BIGINT / 10000
            AS pg_version_num;
    """
    results = db.select_one(sql_raw, params=None)
    pg_version_num = results['pg_version_num']
    return pg_version_num


def get_config_data() -> list:
    """Query Postgres for data about default settings.

    Returns
    --------------------
    results : list
    """
    sql_raw = """
    SELECT default_config_line, name, unit, context, category,
            boot_val, short_desc, frequent_override,
            vartype, min_val, max_val, enumvals,
            boot_val || COALESCE(' ' || unit, '') AS boot_val_display
        FROM pgconfig.settings
        /* Excluding read-only present options.  Not included in delivered
           postgresql.conf files per docs:
            https://www.postgresql.org/docs/current/runtime-config-preset.html
        */
        WHERE category != 'Preset Options'
            /* Configuration options that typically are customized such as
            application_name do not make sense to compare against "defaults"
            */
            AND NOT frequent_override
        ORDER BY name
    ;
    """
    results = db.select_multi(sql_raw)
    return results

def save_config_data(data: list, pg_version_num: int):
    """Pickles config data for reuse later.

    Parameters
    ----------------------
    data : list
        List of dictionaries to pickle.

    pg_version_num : int
        Integer of Postgres version.
    """
    filename = f'../webapp/config/pg{pg_version_num}.pkl'
    with open(filename, 'wb') as data_file:
        pickle.dump(data, data_file)
    print(f'Pickled config data saved to: {filename}')


if __name__ == "__main__":
    run()
