import os
import unittest
from unittest import mock

import config


class ConfigTests(unittest.TestCase):
    def test_default_admin_always_present_and_env_adds_more(self):
        with mock.patch.dict(os.environ, {"DISCORD_TOKEN": "x", "OWNER_IDS": "42, 43"}, clear=False):
            s = config.Settings.load()
        self.assertIn(1530490044098285711, s.owner_ids)
        self.assertTrue({42, 43} <= s.owner_ids)

    def test_admin_without_env_owner_ids(self):
        env = {k: v for k, v in os.environ.items() if k != "OWNER_IDS"}
        env["DISCORD_TOKEN"] = "x"
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(config.Settings.load().owner_ids, {1530490044098285711})


if __name__ == "__main__":
    unittest.main()
