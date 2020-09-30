""" Unit tests to cover the pgconfig module."""
import unittest
import pandas as pd
from webapp import pgconfig

CONFIG_DUPLICATED = """
listen_addresses = '0.0.0.0'
listen_addresses = '*'
listen_addresses = '123.456.12.3'
"""

CONFIG_NO_DUPS = """
listen_addresses = '*'
"""

class PGConfigTests(unittest.TestCase):

    def test_pgconfig_parse_pg_config_returns_Tuple(self):
        result = pgconfig.parse_pg_config()
        expected = tuple
        self.assertEqual(expected, type(result))

    def test_pgconfig_parse_pg_config_returns_DataFrame_first(self):
        result, _ = pgconfig.parse_pg_config()
        expected = pd.DataFrame
        self.assertEqual(expected, type(result))


    def test_pgconfig_parse_pg_config_returns_List_second(self):
        _, result = pgconfig.parse_pg_config()
        expected = list
        self.assertEqual(expected, type(result))


    def test_pgconfig_check_redirect_returns_same_version_with_no_redirect(self):
        version = '9.6'
        expected = version
        new_version = pgconfig.check_redirect(version)
        self.assertEqual(expected, new_version)

    def test_pgconfig_check_redirect_returns_updated_redirect_version(self):
        version = '12beta4'
        expected = '12'
        new_version = pgconfig.check_redirect(version)
        self.assertEqual(expected, new_version)

    def test_pgconfig_compare_custom_config_returns_Dict(self):
        version = '12'
        config_raw = CONFIG_DUPLICATED
        compared, _ = pgconfig.compare_custom_config(version, config_raw)
        stats = pgconfig.custom_config_changes_stats(compared, version)
        expected = dict
        self.assertEqual(expected, type(stats))

    def test_pgconfig_compare_custom_config_detects_param_defined_more_than_once(self):
        version = '12'
        config_raw = CONFIG_DUPLICATED
        _, dups = pgconfig.compare_custom_config(version, config_raw)
        actual = len(dups)
        expected = 3
        self.assertEqual(expected, actual)


    def test_pgconfig_compare_custom_config_no_dups_list_len_zero(self):
        version = '12'
        config_raw = CONFIG_NO_DUPS
        _, dups = pgconfig.compare_custom_config(version, config_raw)
        actual = len(dups)
        expected = 0
        self.assertEqual(expected, actual)
