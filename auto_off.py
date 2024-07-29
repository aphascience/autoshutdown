import subprocess
import argparse
import os
import logging
import logging.handlers

# default paths
LOADAVG_FILEPATH = "/proc/loadavg"
LOGGING_FILEPATH = "/var/log/auto-off.log"
# use non-persistent directory
LOADAVG_RECORD_FILEPATH = "/tmp/loadavg_record"
LOADAVG_INDEX = {1: 0, 5: 1, 15: 2}


class Config:
    """
        Validates and stores configuration settings for auto_off routine
    """
    def __init__(self,
                 inactivity_threshold_mins: int,
                 loadavg_level_mins: int = 15,
                 cpu_idle_threshold: float = 0.05,
                 ssh_check: bool = True):
        """
        Params:
            inactivity_threshold_mins (int): minutes of inactivity before
                shutdown
            loadavg_level_mins (int): size of window (in minutes) on which to
                measure CPU load
            cpu_idle_threshold (float): threshold of CPU load defining
                'inactive'
            ssh_check (bool): switch for checking for open SSH connections
        """
        self.inactivity_threshold_mins = inactivity_threshold_mins
        self.loadavg_level_mins = loadavg_level_mins
        self.cpu_idle_threshold = cpu_idle_threshold
        self.ssh_check = ssh_check
        self._validate_config()
        self.num_periods = self._set_num_periods()

    def _set_num_periods(self) -> int:
        """
            num_periods (int) is the number of consecutive load_avg measures
            that must fall bellow 'cpu_idle_threshold' in order to determine
            'inactivtiy'
        """
        return int(self.inactivity_threshold_mins /
                   self.loadavg_level_mins)

    def _validate_config(self):
        if not isinstance(self.ssh_check, bool):
            raise TypeError("'ssh_check' must be a Boolean")
        if self.cpu_idle_threshold > 1 or self.cpu_idle_threshold < 0:
            raise ValueError("'cpu_idle_threshold' must be between 0 and 1")
        if not validate_loadavg_level(self.loadavg_level_mins):
            raise ValueError("'loadavg_level_mins' must be one of 1, 5 or 15")
        if not validate_inactivity_threshold(self.inactivity_threshold_mins,
                                             self.loadavg_level_mins):
            raise ValueError("'inactivity_threshold_mins' must a multiple of "
                             f"{self.loadavg_level_mins}")


def validate_inactivity_threshold(inactivity_threshold_mins: int,
                                  loadavg_level_mins: int) -> bool:
    """
        Returns True if inactivity window is a multple of window_size,
        otherwise returns False
    """
    return inactivity_threshold_mins % loadavg_level_mins == 0


def validate_loadavg_level(loadavg_level_mins: int) -> bool:
    """
        Returns True if loadavg_level is one of 1, 5, or 15, otherwise returns
        False
    """
    return loadavg_level_mins in LOADAVG_INDEX.keys()


def get_loadavg(loadavg_level_mins: int = 1,
                loadavg_filepath: str = LOADAVG_FILEPATH) -> str:
    """
        Reads the loadavg file and returns the load average for the given
        loadavg_level in minutes

        loadavg_level must be one of 1, 5, or 15.
    """
    with open(loadavg_filepath) as f:
        contents = f.read().split()
    return contents[LOADAVG_INDEX[loadavg_level_mins]]


def cpu_inactive(config: Config,
                 loadavg_record_filepath:
                 str = LOADAVG_RECORD_FILEPATH) -> bool:
    """
        Returns:
            True: if the machine is deemed inactive
            False: if the machine is deemed active
            False: if the machine is in the 'inactivity threshold'

        'Active' state is achieved if any of the latest 'num_periods' load
        average values is greater than 'cpu_idle_threshold'

        'Inactivity' is determined by 'num_periods' consecutive load avergae
        values falling bellow 'cpu_idle_threshold'
    """
    with open(loadavg_record_filepath, mode="a") as f:
        f.write(f"{get_loadavg(config.loadavg_level_mins)}\n")
    # need to close and reopen to move the file pointer
    with open(loadavg_record_filepath, mode="r") as f:
        loadavg_record = f.read().splitlines()
    if float(loadavg_record[-1]) < config.cpu_idle_threshold:
        if len(loadavg_record) >= config.num_periods:
            if any([float(i) >= config.cpu_idle_threshold for i in
                    loadavg_record[-config.num_periods:-1]]):
                logging.info("inside inactivity window")
                return False
            else:
                logging.info("shutting down machine")
                return True
        else:
            logging.info("inside inactivity window")
            return False
    logging.info("system busy")
    return False


def ssh_connections() -> bool:
    """
        Returns True if there are open SSH connections, returns False
        otherwise
    """
    output = subprocess.check_output("ss -o state established '( dport = :ssh or sport = :ssh )'",
                                     shell=True)
    return output.count(b'\n') > 1


def shutdown_approved(config: Config,
                      loadavg_record_filepath:
                      str = LOADAVG_RECORD_FILEPATH) -> bool:
    """
        Combines checks on SSH connections and CPU activity

        Returns True if the system should shutdown, returns False otherwise

        Logs the outcome
    """
    if config.ssh_check:
        if ssh_connections():
            logging.info("SSH connection open")
            return False
    return cpu_inactive(config, loadavg_record_filepath)


def routine(config: Config,
            loadavg_record_filepath: str = LOADAVG_RECORD_FILEPATH):
    """
        Main routine to shutdown machine. Determines if shutdown state is
        achieved and shutdowns the machine accordingly
    """
    if not os.path.isfile(loadavg_record_filepath):
        logging.info("Starting auto-off routine: machine will shutdown after "
                     f"{config.inactivity_threshold_mins} minutes of "
                     "inactivity")
        open(loadavg_record_filepath, "x")
    if shutdown_approved(config, loadavg_record_filepath):
        subprocess.run(["/usr/sbin/shutdown", "now"])


if __name__ == "__main__":
    # setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s",
                        datefmt='%d/%m/%Y %I:%M:%S %p',
                        handlers=[logging.StreamHandler(),
                                  logging.handlers.RotatingFileHandler(
                                      LOGGING_FILEPATH,
                                      maxBytes=16000,
                                      backupCount=2)])
    try:
        # Parse
        parser = argparse.ArgumentParser()
        parser.add_argument("--inactivity_threshold_mins",
                            help="minutes of inactivity before shutdown",
                            default=15, type=int)
        parser.add_argument("--loadavg_level_mins",
                            help="size of window (in minutes) on which to "
                            "measure CPU load",
                            default=15, type=int)
        parser.add_argument("--cpu_idle_threshold",
                            help="threshold of CPU load defining inactive",
                            default=0.05, type=float)
        parser.add_argument("--ssh", action="store_true", default=False,
                            help="switch for checking for open SSH connections")
        args = parser.parse_args()
        config = Config(args.inactivity_threshold_mins,
                        args.loadavg_level_mins,
                        args.cpu_idle_threshold,
                        args.ssh)
        routine(config)
    except Exception as e:
        logging.error(e, exc_info=True)
