"""Generates config based on pgconfig.settings.
"""
import db

def run():
    """Generates config from defined database connection.
    """
    db.prepare()
    default_config = get_defaults()
    save_config(data=default_config)


def get_defaults():
    """Queries Postgres for default settings.

    Returns
    --------------------
    results : list
    """
    sql_raw = """
    SELECT default_config_line
        FROM pgconfig.settings
        WHERE NOT frequent_override
            AND category != 'Preset Options'
    ;
    """
    results = db.select_multi(sql_raw)
    return results

def save_config(data, filename='postgresql.conf.default'):
    """Saves configuration file from `data`.

    Parameters
    ---------------------
    data : list
    filename : str
        Defaults to postgresql.conf.default
    """
    # Repack w/out the dict portion
    lines = list()
    for row in data:
        line = row['default_config_line']
        lines.append(line)

    print(f'Saving config data to {filename}')
    # Write to file
    with open(filename, 'w') as f:
        f.writelines('%s\n' % l for l in lines)


if __name__ == "__main__":
    run()
