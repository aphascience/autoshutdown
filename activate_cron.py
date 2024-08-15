import os
import datetime
import argparse
import sys
from typing import Callable, List

import auto_off
from rich import prompt
from rich import print as richprint
from beaupy import confirm as bpyconfirm
from beaupy import Config as BpyConfig
from packaging.version import Version


DEFAULT_CRON_FILEPATH = "/etc/cron.d/auto_off"
DEFAULT_VERSION_FILEPATH = "version.properties"


class AutoOffConfig:
    """
        Stores configuration settings to be written to crontab
    """
    def __init__(self,
                 shutdown_time: datetime.time,
                 inactivity_threshold_mins: int,
                 loadavg_level_mins: int = 15,
                 cpu_idle_threshold: float = 0.05,
                 ssh_check: bool = True,
                 default_shutdown_at_midnight: bool = True):
        self._shutdown_time = shutdown_time
        self.inactivity_threshold_mins = inactivity_threshold_mins
        self.loadavg_level_mins = loadavg_level_mins
        self.cpu_idle_threshold = cpu_idle_threshold
        self.ssh_check = ssh_check
        self.default_shutdown_at_midnight = default_shutdown_at_midnight
        self._validate_config()
        self.routine_first_run_time = \
            get_first_run_time(self._shutdown_time,
                               self.inactivity_threshold_mins,
                               self.loadavg_level_mins)

    # TODO: maybe this is unecesary now since all inputs are validated in parse_config()
    def _validate_config(self):
        if not isinstance(self._shutdown_time, datetime.time):
            raise TypeError("'shutdown_time' must be a datetime.time object")
        if not isinstance(self.ssh_check, bool):
            raise TypeError("'ssh_check' must be a Boolean")
        if not isinstance(self.default_shutdown_at_midnight, bool):
            raise TypeError("'default_shutdwon_at_midnight' must be a Boolean")
        if self.cpu_idle_threshold > 1 or self.cpu_idle_threshold < 0:
            raise ValueError("'threshold' must be between 0 and 1")
        if not auto_off.validate_loadavg_level(self.loadavg_level_mins):
            raise ValueError("'loadavg_level_mins' must be one of 1, 5 or 15")
        if not auto_off.validate_inactivity_threshold(self.inactivity_threshold_mins,
                                                      self.loadavg_level_mins):
            raise ValueError(f"'inactivity_threshold_mins' must a multiple of {self.loadavg_level_mins}")


class ShutdownTimePrompt(prompt.PromptBase[int]):

    response_type = datetime.time
    validate_error_message = ("[red]Please enter a time in 24hr format, "
                              "i.e. 0000 - 2359")

    def process_response(self, value: str) -> datetime.time:
        if not len(value) == 4:
            raise prompt.InvalidResponse(self.validate_error_message)
        try:
            return datetime.time(int(value[:2]), int(value[2:]))
        except ValueError:
            raise prompt.InvalidResponse(self.validate_error_message)


class CPUIdlePrompt(prompt.PromptBase[float]):

    response_type = float
    validate_error_message = "[red]Please enter a number between 0 and 1"

    def process_response(self, value: str) -> float:
        try:
            value_float = float(value)
        except ValueError:
            raise prompt.InvalidResponse(self.validate_error_message)
        if value_float > 1 or value_float < 0:
            raise prompt.InvalidResponse(self.validate_error_message)
        else:
            return value_float


def parsing_validation(method: Callable, *args, **kwargs):
    """
        Essentially just a wrapper for 'method' which encapsulates
        exceptions resulting from badly formatted configuration. It's
        only used on 'AutoOffConfig'.
    """
    try:
        return method(*args, **kwargs)
    except (ValueError, TypeError) as e:
        raise Exception(f"Malformatted configuration: {e}")


def get_first_run_time(shutdown_time: datetime.time,
                       inactivity_threshold_mins: int,
                       loadavg_level_mins: int) -> datetime.time:
    """
        Gets the first run time for auto_off.py
        routine_first_run_time is the "set back" from the desired shutdown
        time by ( inactivity_threshold_mins - loadavg_level_mins )
        - it enables the machine to shutdown as early as the the desired
        shutdown time if the CPU was "inactive" for the previous
        inactivity_threshold_mins

        e.g. shutdown_time = 1800, inactivity_threshold_mins = 45, loadavg_level_min = 15:
        routine_first_run_time = 1730
        when running for the 1st time at 1730, it measures CPU loadavg for the time 1715-1730,
        when running for the 2nd time at 1745, it measures CPU loadavg for the time 1730-1745,
        when running for the 3rd time at 1800, it measures CPU loadavg for the time 1745-1800
        the machine will shutdown at 1800 if CPU loadavg is <
        cpu_idle_threshold for all three measurements

        If the calculation of first run time goes beyond 0000, i.e. into the
        next day, a ValueError is raised
    """
    try:
        return (datetime.datetime.combine(datetime.date(1, 1, 1),
                shutdown_time) -
                datetime.timedelta(minutes=(inactivity_threshold_mins -
                                   loadavg_level_mins))).time()
    except OverflowError:
        raise ValueError("shutdown time, loadavg level and "
                         "inactivity threshold are incompatible. Try "
                         "reducing inactivity_threshold_mins or setting a "
                         "later shutdwown_time")


def enable_auto_off() -> bool:
    """
        Prompts user for confirmation of whether they want to enable
        or disbale auto_off.

        Returns a boolean: True for enable, False for disable
    """
    BpyConfig.raise_on_interrupt = True
    return bpyconfirm("Would you like to enable/disable auto_off?",
                      yes_text="enable",
                      no_text="disable",
                      default_is_yes="true",
                      char_prompt=False)


def get_inactivity_threshold_choices(loadavg_level_mins: int,
                                     shutdown_time: datetime.time) -> List[str]:
    """
        inactivity_threshold_choices are all multiples of loadavg_level_mins
        upto a maximum value such that the first possible time our cron job
        runs is at 0000
    """
    return [str(i) for i in
            range(loadavg_level_mins, shutdown_time.hour * 60 +
                  shutdown_time.minute + loadavg_level_mins + 1,
                  loadavg_level_mins)]


def parse_version_number(version_filepath: str = DEFAULT_VERSION_FILEPATH) \
        -> Version:
    """
        Parses the autoshutdown version number from version.properties file
        into an instance of packaging.version.Version.

        Raises InvalidVersion - If the version does not conform to PEP 440 in
        any way then this exception will be raised.
    """
    with open(version_filepath) as f:
        version_string = f.readline()
    return Version(version_string)


def parse_config() -> AutoOffConfig:
    """
        Parses the user specified configuration parameters read in via
        CLI at runtime using beaupy and rich packages.

        Returns an instance of AutoOffConfig, holding the required
        configuration parameters
    """
    compatible = False
    while not compatible:
        shutdown_time_prompt = ShutdownTimePrompt()
        shutdown_time = \
            shutdown_time_prompt.ask("Choose shutdown time in 24hr format, e.g. "
                                     "1830 (this is the earliest your machine "
                                     "will shutdown) [bold][bright_cyan](1800)",
                                     default=datetime.time(18, 00))
        loadavg_level_mins = \
            int(prompt.IntPrompt.ask("Choose loadavg level (if unsure, "
                                     "just press enter to select the default)",
                                     choices=["1", "5", "15"], default="15"))
        inactivity_threshold_choices = \
            get_inactivity_threshold_choices(loadavg_level_mins, shutdown_time)
        if len(inactivity_threshold_choices) > 4:
            inactivity_threshold_choices_str = \
                (f"[bold][bright_magenta][{'/'.join(inactivity_threshold_choices[:3])}"
                 f" ... {inactivity_threshold_choices[-1]}]")
        else:
            inactivity_threshold_choices_str = \
                f"[bold][bright_magenta][{'/'.join(inactivity_threshold_choices[:])}]"
        default_inactivty_threshold = str(min(inactivity_threshold_choices,
                                              key=lambda x: abs(int(x)-30)))
        inactivity_threshold_mins = \
            int(prompt.IntPrompt.ask("Choose inactivity threshold (mins), "
                                     "(auto_off will wait this many minutes "
                                     "after CPU load has dropped below an idle"
                                     " threshold before switching your machine"
                                     " off) "
                                     f"[bold][bright_magenta]{inactivity_threshold_choices_str}",
                                     default=default_inactivty_threshold,
                                     show_choices=False,
                                     choices=inactivity_threshold_choices))
        try:
            compatible = True
        except ValueError as e:
            richprint(f"[red]{e}")

    cpu_idle_prompt = CPUIdlePrompt()
    cpu_idle_threshold = \
        cpu_idle_prompt.ask("Choose CPU idle threshold (if unsure, just "
                            "press enter to select the default) "
                            "[bold][bright_cyan](0.05)",
                            default=0.05)
    ssh_check = \
        prompt.Confirm.ask("Ensure no SSH connections are open before "
                           "switching off your machine?", default=True)
    default_shutdown_at_midnight =\
        prompt.Confirm.ask("Would you like your machine to shutdown at "
                           "midnight, even if the above criteria are not met? "
                           "(if unsure, just press enter to select yes)",
                           default=True)
    return parsing_validation(AutoOffConfig,
                              shutdown_time=shutdown_time,
                              inactivity_threshold_mins=inactivity_threshold_mins,
                              loadavg_level_mins=loadavg_level_mins,
                              cpu_idle_threshold=cpu_idle_threshold,
                              ssh_check=ssh_check,
                              default_shutdown_at_midnight=default_shutdown_at_midnight)


def build_cron_string(config: AutoOffConfig, auto_off_path: str) -> str:
    """
        Constructs and returns a string to write to `/etc/crontab`,
        i.e. defines the auto_off cronjob(s)

        Makes two lines (jobs) for the `/etc/crontab` file:
            - The first job (`cron_hr_1`) schedules `auto_off.py` up to the
              first full hour after `config.shutdown_time`.
            - The second job (`cron_all`) schedules `auto_off.py` from the
              first full hour after `config.shutdown_time` until 2400
              (midnight).

        The return value is a two line string, e.g.
            `cron_hr_1` + "\n" + `cron_hr_2`

        This is required for instances where `config.shutdown_time` doesn't
        fall on the hour. (See inline comments below for example)
    """
    if not isinstance(config, AutoOffConfig):
        raise TypeError("Invalid input arg: config must be an instance of AutOffConfig")
    # e.g. if shutdown_time = 2030 and config.loadavg_level_mins = 10:
    # then start_hour = 20, start_minute = 30
    start_hour = config.routine_first_run_time.hour
    start_minute = config.routine_first_run_time.minute
    cron_general = (f"* * * root {auto_off_path} "
                    f"{parse_version_number()} "
                    f"--inactivity_threshold_mins {config.inactivity_threshold_mins} "
                    f"--loadavg_level_mins {config.loadavg_level_mins} "
                    f"--cpu_idle_threshold {config.cpu_idle_threshold}"
                    f"{' --ssh' if config.ssh_check else ''}")

    # e.g. hr_1_minutes = "30,45"
    hr_1_minutes = ",".join([str(i) for i in range(start_minute, 60,
                                                   config.loadavg_level_mins)])
    # e.g. all_minutes = "15,30,45"
    all_minutes = ",".join([str(i) for i in range(int(
        hr_1_minutes.split(",")[-1]) + config.loadavg_level_mins - 60, 60,
        config.loadavg_level_mins)])

    # e.g. cron_hr_1 = f"30,45 20 root auto_off.py --inactivity_threshold_mins 15
    #   --loadavg_level_mins 15 --load_cpu_idle_threshold 0.05 --ssh"
    cron_hr_1 = f"{hr_1_minutes} {start_hour} {cron_general}\n"

    if start_hour == 22:
        # e.g. cron_all = f"15,30,45 23 root auto_off.py
        #   --inactivity_threshold_mins 15 --loadavg_level_mins 15
        #   --load_cpu_idle_threshold 0.05 --ssh"
        cron_all = f"{all_minutes} 23 {cron_general}\n"
    elif start_hour == 23:
        # i.e. cron_hour_1 runs up to midnight
        cron_all = ""
    else:
        # i.e. start_hour < 22
        # e.g. cron_all = f"15,30,45 20-23  root auto_off.py
        #   --inactivity_threshold_mins 15 --loadavg_level_mins 15
        #   --load_cpu_idle_threshold 0.05 --ssh"
        cron_all = f"{all_minutes} {start_hour + 1}-23 {cron_general}\n"

    # e.g. the full return value (formatted as text) might look something like:
    #       30,45 20 * * * root auto_off.py --inactivity_threshold_mins 15 --loadavg_level_mins 15 --load_cpu_idle_threshold 0.05 --ssh
    #       15,30,45 21-23 * * * root auto_off.py --inactivity_threshold_mins 15 --loadavg_level_mins 15 --load_cpu_idle_threshold 0.05 --ssh
    if config.default_shutdown_at_midnight:
        return cron_hr_1 + cron_all + "0 00 * * * root /usr/sbin/shutdown now\n"
    else:
        return cron_hr_1 + cron_all


def activate_cron(cron_string: str,
                  cron_filepath: str = DEFAULT_CRON_FILEPATH):
    """
        Creates the cron file at 'cron_filepath' and writes
        cron_string to the newly created file.

        Raises FileExistsError if the cron file exists
    """
    try:
        with open(cron_filepath, "x") as crontab:
            crontab.write(cron_string)
    except FileExistsError:
        raise FileExistsError(f"Ensure cron file ('{cron_filepath}') is "
                              "removed before calling 'active_cron()'")


def deactivate_cron(cron_filepath: str = DEFAULT_CRON_FILEPATH):
    """
        Deletes an existing cron file at 'cron_filepath'
    """
    try:
        os.remove(cron_filepath)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Aborting: activate_cron must be run with sudo")
    parser = argparse.ArgumentParser()
    parser.add_argument("--auto_off_path",
                        help="path to auto_off executable",
                        default=f"{os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]}/auto_off")
    args = parser.parse_args()
    try:
        if enable_auto_off():
            config = parse_config()
            deactivate_cron()
            activate_cron(build_cron_string(config, args.auto_off_path))
            print("Auto-off enabled")
        else:
            deactivate_cron()
            print("Auto-off disabled")
    except KeyboardInterrupt:
        print("\nAbborting auto_off configuration, leaving configuration "
              "unchanged")
