import unittest
from unittest.mock import patch
import datetime

from pyfakefs import fake_filesystem_unittest

import auto_off
import activate_cron


class TestConfigureAutoOff(unittest.TestCase):
    def test_build_cron_string(self):
        self.maxDiff = 1023
        # invalid input
        with self.assertRaises(TypeError):
            activate_cron.build_cron_string("foo")

        # routine first run hour < 23
        config = activate_cron.AutoOffConfig(datetime.time(21, 00),
                                             30, 15, 0.05, True, False)
        expected = "45 20 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n0,15,30,45 21-23 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n"
        self.assertEqual(activate_cron.build_cron_string(config, "foo/auto_off"),
                         expected)

        # routine first run hour == 22
        config = activate_cron.AutoOffConfig(datetime.time(22, 15),
                                             30, 15, 0.05, True, False)
        expected = "0,15,30,45 22 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n0,15,30,45 23 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n"
        self.assertEqual(activate_cron.build_cron_string(config, "foo/auto_off"),
                         expected)

        # start_hour == 23
        config = activate_cron.AutoOffConfig(datetime.time(23, 15),
                                             30, 15, 0.05, True, False)
        expected = "0,15,30,45 23 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n"
        self.assertEqual(activate_cron.build_cron_string(config, "foo/auto_off"),
                         expected)

        # routine first run hour == 22 with default midnight shutdown
        config = activate_cron.AutoOffConfig(datetime.time(22, 15),
                                             30, 15, 0.05, True, True)
        expected = "0,15,30,45 22 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n0,15,30,45 23 * * * root foo/auto_off --inactivity_threshold_mins 30 --loadavg_level_mins 15 --cpu_idle_threshold 0.05 --ssh\n0 00 * * * root /usr/sbin/shutdown now\n"
        self.assertEqual(activate_cron.build_cron_string(config, "foo/auto_off"),
                         expected)

    def test_get_inactivity_threshold_choices(self):
        shutdown_time = datetime.time(0, 0)
        choices = activate_cron.get_inactivity_threshold_choices(15,
                                                                 shutdown_time)
        self.assertEqual(choices, ["15"])
        choices = activate_cron.get_inactivity_threshold_choices(1,
                                                                 shutdown_time)
        self.assertEqual(choices, ["1"])
        shutdown_time = datetime.time(10, 0)
        choices = activate_cron.get_inactivity_threshold_choices(15,
                                                                 shutdown_time)
        self.assertEqual(choices[0], "15")
        self.assertEqual(choices[-1], "615")

        shutdown_time = datetime.time(23, 59)
        choices = activate_cron.get_inactivity_threshold_choices(15,
                                                                 shutdown_time)
        self.assertEqual(choices[0], "15")
        self.assertEqual(choices[-1], "1440")

    def test_get_first_run_time(self):
        shutdown_time = datetime.time(0, 0)
        first_run_time = activate_cron.get_first_run_time(shutdown_time,
                                                          15, 15)
        self.assertEqual(first_run_time, datetime.time(0, 0))
        shutdown_time = datetime.time(18, 0)
        first_run_time = activate_cron.get_first_run_time(shutdown_time,
                                                          30, 15)
        self.assertEqual(first_run_time, datetime.time(17, 45))
        shutdown_time = datetime.time(10, 0)
        first_run_time = activate_cron.get_first_run_time(shutdown_time,
                                                          615, 15)
        self.assertEqual(first_run_time, datetime.time(0, 0))
        shutdown_time = datetime.time(0, 0)
        with self.assertRaises(ValueError):
            activate_cron.get_first_run_time(shutdown_time, 2, 1)
        with self.assertRaises(ValueError):
            activate_cron.get_first_run_time(shutdown_time, 15, 5)
        with self.assertRaises(ValueError):
            activate_cron.get_first_run_time(shutdown_time, 30, 15)
        shutdown_time = datetime.time(10, 0)
        with self.assertRaises(ValueError):
            activate_cron.get_first_run_time(shutdown_time, 630, 15)


class TestAutoOff(fake_filesystem_unittest.TestCase):
    def setUp(self):
        """
            Set up method
        """
        # use "fake" in-memory filesystem
        self.setUpPyfakefs()

    def tearDown(self):
        """
            Tear down method
        """
        pass

    @patch("auto_off.logging.info")
    def test_cpu_inactive(self, mock_logging_info):
        # setup config object
        config = auto_off.Config(15)

        # tests an inactivte CPU with a window of one cycle
        self.fs.create_file("test_record_filepath")
        with patch("auto_off.get_loadavg") as mock_get_loadavg:
            mock_get_loadavg.return_value = "0"
            self.assertTrue(auto_off.cpu_inactive(config,
                                                  "test_record_filepath"))
            mock_logging_info.assert_called_with("shutting down machine")
        self.fs.remove_object("test_record_filepath")

        # tests an activte CPU with a window of one cycle
        self.fs.create_file("test_record_filepath")
        with patch("auto_off.get_loadavg") as mock_get_loadavg:
            mock_get_loadavg.return_value = "2"
            self.assertFalse(auto_off.cpu_inactive(config,
                                                   "test_record_filepath"))
            mock_logging_info.assert_called_with("system busy")
        self.fs.remove_object("test_record_filepath")

        # tests an inactivte CPU with a window of two cycles
        config.num_periods = 2
        self.fs.create_file("test_record_filepath")
        with patch("auto_off.get_loadavg") as mock_get_loadavg:
            mock_get_loadavg.return_value = "0"
            self.assertFalse(auto_off.cpu_inactive(config,
                                                   "test_record_filepath"))
            mock_logging_info.assert_called_with("inside inactivity window")
            self.assertTrue(auto_off.cpu_inactive(config,
                                                  "test_record_filepath"))
            mock_logging_info.assert_called_with("shutting down machine")
        self.fs.remove_object("test_record_filepath")

        # tests an CPU in states: inactive, active, inactive, inactive with a window of two cycles
        self.fs.create_file("test_record_filepath")
        with patch("auto_off.get_loadavg") as mock_get_loadavg:
            mock_get_loadavg.side_effect = ["0", "1", "0", "0"]
            self.assertFalse(auto_off.cpu_inactive(config,
                                                   "test_record_filepath"))
            mock_logging_info.assert_called_with("inside inactivity window")
            self.assertFalse(auto_off.cpu_inactive(config,
                                                   "test_record_filepath"))
            mock_logging_info.assert_called_with("system busy")
            self.assertFalse(auto_off.cpu_inactive(config,
                                                   "test_record_filepath"))
            mock_logging_info.assert_called_with("inside inactivity window")
            self.assertTrue(auto_off.cpu_inactive(config,
                                                  "test_record_filepath"))
            mock_logging_info.assert_called_with("shutting down machine")


if __name__ == '__main__':
    unittest.main()
