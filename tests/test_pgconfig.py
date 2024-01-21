""" Unit tests to cover the pgconfig module."""
import unittest
import pandas as pd
from webapp import pgconfig


class PGConfigTests(unittest.TestCase):

    def test_pgconfig_check_redirect_returns_same_version_with_no_redirect(self):
        version = '10'
        expected = version
        new_version = pgconfig.check_redirect(version)
        self.assertEqual(expected, new_version)

    def test_pgconfig_check_redirect_returns_updated_redirect_version(self):
        version = '12beta4'
        expected = '12'
        new_version = pgconfig.check_redirect(version)
        self.assertEqual(expected, new_version)


    def test_pgconfig_config_changes_returns_expected_type(self):
        vers1 = 12
        vers2 = 16
        result = pgconfig.config_changes(vers1=vers1, vers2=vers2)
        actual = type(result)
        expected = pd.DataFrame
        self.assertEqual(expected, actual)

    def test_pgconfig_config_changes_raises_ValueError_when_misordered_versions(self):
        vers1 = 16
        vers2 = 12
        self.assertRaises(ValueError, pgconfig.config_changes, vers1, vers2)

    def test_load_config_data_raises_ValueError_when_invalid_version(self):
        vers1 = -999
        self.assertRaises(ValueError, pgconfig.load_config_data, vers1)
