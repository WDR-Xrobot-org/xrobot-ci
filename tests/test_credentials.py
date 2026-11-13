import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('helper', Path(__file__).parents[1] / 'ci/credential_helper.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class CredentialScope(unittest.TestCase):
    def test_selected_organization(self):
        self.assertIn('password=test-only', helper.credentials('protocol=https\nhost=github.com\npath=WDR-Xrobot-org/Pitch.git\n', 'test-only'))

    def test_other_repositories_receive_no_secret(self):
        for path in ['xrobot-org/libxr.git', 'YunMo-yanyu/Pitch.git', 'WDR-Xrobot-org-other/Pitch.git']:
            self.assertEqual('', helper.credentials('protocol=https\nhost=github.com\npath=' + path, 'test-only'))

    def test_other_hosts_receive_no_secret(self):
        self.assertEqual('', helper.credentials('protocol=https\nhost=example.com\npath=WDR-Xrobot-org/Pitch.git', 'test-only'))

    def test_missing_token(self):
        self.assertEqual('', helper.credentials('protocol=https\nhost=github.com\npath=WDR-Xrobot-org/Pitch.git', ''))
