
DROP VIEW IF EXISTS pgconfig.settings;
CREATE VIEW pgconfig.settings AS
SELECT name, setting, context, source, reset_val, boot_val,
        unit, category,
        name || ' = ' ||  CHR(39) || current_setting(name) || CHR(39)
            AS postgresconf_line,
        name || ' = ' || CHR(39) || 
                -- Recalculates 8kB units to more comprehensible kB units.
                -- above line gets to use the current_setting() func, didn't find any
                -- such option for this one
                CASE WHEN boot_val = '-1' THEN boot_val
                        WHEN unit = '8kB' THEN ((boot_val::numeric * 8)::BIGINT)::TEXT
                        ELSE boot_val 
                        END
                || COALESCE(CASE WHEN boot_val = '-1' THEN NULL
                                WHEN unit = '8kB' THEN 'kB'
                                ELSE unit
                                END, '') || CHR(39)
            AS default_config_line,
        short_desc,
        CASE WHEN name LIKE 'lc%'
                THEN True
             WHEN name LIKE 'unix%'
                THEN True
            WHEN name IN ('application_name', 'TimeZone', 'timezone_abbreviations',
                          'default_text_search_config')
                THEN True
            WHEN category IN ('File Locations')
                THEN True
            ELSE False
            END AS frequent_override,
        CASE WHEN boot_val = setting THEN True 
            ELSE False 
            END AS system_default,
        CASE WHEN reset_val = setting THEN False 
            ELSE True
            END AS session_override, 
        pending_restart
    FROM pg_catalog.pg_settings
;

COMMENT ON COLUMN pgconfig.settings.postgresconf_line IS 'Current configuration in format suitable for postgresql.conf.  All setting values quoted in single quotes since that always works, and omitting the quotes does not.';
COMMENT ON COLUMN pgconfig.settings.default_config_line IS 'Postgres default configuration for setting. Some are hard coded, some are determined at build time.';
