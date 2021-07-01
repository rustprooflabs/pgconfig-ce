import db

def run():
    db.prepare()
    default_config = _get_defaults()
    _save_config(data=default_config)


def _get_defaults():
    sql_raw = """
    SELECT default_config_line
        FROM pgconfig.settings
        WHERE NOT frequent_override
            AND category != 'Preset Options'
    ;
    """
    results = db.select_multi(sql_raw)
    return results

def _save_config(data, filename='postgresql.conf.default'):
    # Repack w/out the dict portion
    lines = list()
    for row in data:
        line = row['default_config_line']
        lines.append(line)

    print(f'Saving config data to {filename}')
    # Write to file
    with open(filename, 'w') as f:
        f.writelines('%s\n' % l for l in lines)


