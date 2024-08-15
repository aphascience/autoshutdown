# Auto Shutdown

## Contents
1. [What it does](#what-it-does)
1. [Build](#build)
1. [Activating autoshutdown](#activating-autoshutdown)
1. [Deactivate or reconfigure](#deactivate-or-reconfigure)
1. [How it works](#how-it-works)
1. [Logs](#logs)

## What it does

* Automatic shutdown of linux servers / virtual machines / EC2 instances.
* It can be configured to shutdown your machine at a specific time every day.
* Shutdown will be blocked whilst you are connected to the machine. This means, if you are working beyond the specified shutdown time, your machine will remain on until you have disconnected.
* Shutdown will be blocked whilst processes are running on the machine. This means you can set a large job running into the evening and disconnect from the machine without worrying that the machine will switch off before your job has completed. 

## Build

Building the software uses [PyInstaller](https://pyinstaller.org/en/stable/) which bundles all dependencies and the python interpreter into a single executable ready for use. 

The software is built with Python3.12. This means you will need to have Python3.12 installed in order to build. 

To build the binaries, just run:

```
make
```

This will make a folder called `autoshutdown_vX.X.X`.

`autoshutdown_vX.X.X` contains two executable files, `activate_cron` and `auto_off` as well as a folder called `_internal` which contains shared libraries for our executables. 

In a little more detail, calling `make` runs `build.sh` which does the following: 

1. creates a Python3.12 virtual environment
1. installs python dependencies, including `pyinstaller` into the virtual environment
1. runs `pyinstaller` using the virtual environment to build the binaries
1. moves binaries into a single distribution folder
1. deletes the virtual environment

## Activating autoshutdown

Once built, the auto off system can be configured by running:

```
sudo autoshutdown_vX.X.X/activate_cron
```

You will then be guided through a number of command line prompts:

1. `Would you like to enable/disable auto_off?`
     - by selecting "enable", you will be guided further through the configuration process.
     - by selecting "disable", autoshutdown will be disabled and the configuration process will be ended.

2. `Choose shutdown time in 24hr format, e.g. 1830 (this is the earliest your machine will shutdown) (1800) (18:00:00)`
    
    - this is asking what time you want your machine to shutdown if you are not using it or if nothing is running on the machine.
    - a sensible choice might be 6pm, which is the default, and can be selected by simply pressing enter.

3. `Choose loadavg level (if unsure, just press enter to select the default) [1/5/15] (15)` 
    - for most users the default value of 15 will be the right choice. Simply press enter to select this value.

4. `Choose inactivity threshold (mins), (auto_off will wait this many minutes after CPU load has dropped below an idle threshold before switching your machine off) [15/30/45 ... 1095] (30)` 
    - it can be useful to ask autoshutdown to wait a specified number of minutes after an unattended process has finished before switching off your virtual machine.
    - choose one of the presented options, or just press enter to choose the default.

5. `Choose CPU idle threshold (if unsure, just press enter to select the default) (0.05)` 
    - for most users the default value of 0.05 will be the right choice. Simply press enter to select this value.

6. `Ensure no SSH connections are open before switching off your machine? [y/n] (y)` 
    - selecting "yes" (recommended) means that autoshutdown will be blocked whilst you are connected to the machine.
    - if "no" is selected, your machine may shutdown whilst you are using it.

7. `Would you like your machine to shutdown at midnight, even if the above criteria are not met? (if unsure, just press enter to select yes) [y/n] (y)` 
    - finally, you are asked if you would like your machine to shutdown at midnight, even if all other criteria are not met.
    - unless you plan to run jobs overnight, we strongly recommend you select yes.

## Deactivate or reconfigure

If you want to deactivate autoshutdown, simply rerun `sudo autoshutdown_VX.X.X/activate_cron` and select "disable" at the first prompt.

If you want to change the configuration, simply rerun `sudo autoshutdown_VX.X.X/activate_cron`, select "enable" at the first prompt and continue to run through the configuration setup.

## How it works

* autoshutdown is written in Python.
* There are two main programs. The first, configures autoshutdown according to your specified configuration settings and is run when you run `sudo activate_cron`. It reads the answers you give to each prompt and creates a custom "[cron job](https://en.wikipedia.org/wiki/Cron)" accordingly.
* The resulting cron file is written to `/etc/cron.d/auto_off`.
* This cron file schedules the second autoshutdown program to automatically run at at specific time everyday.
* When the second program runs, it checks that there are no active SSH connection open, that the machine is not currently running an unattended job, and finally that the machine has been "inactive" for the specified number of minutes. If all of these criteria are met, the machine will be shutdown.
* The program determines if unattended jobs are running by reading the CPU load from the loadavg file, `/proc/loadavg`.

## Logs

`auto_off` saves a log to `/var/log/auto-off.log`.

For example, the log file could look like:

```
13/05/2024 05:45:01 PM - Starting auto-off routine: machine will shutdown after 30 minutes of inactivity
13/05/2024 05:45:01 PM - SSH connection open
13/05/2024 06:00:01 PM - SSH connection open
13/05/2024 06:15:01 PM - SSH connection open
13/05/2024 06:30:01 PM - system busy
13/05/2024 06:45:02 PM - system busy
13/05/2024 07:00:01 PM - inside inactivity window
13/05/2024 07:15:01 PM - shutting down machine
```

This tells us that:
1. `Starting auto-off routine` indicates that the auto off routine started at 5:45pm, the earliest it will shutdown is 6pm
1. `SSH connection open` indicates that for the next 3 time steps, the machine had an open SSH connection, so shutdown was blocked
1. `system busy` indicates that for the next 2 time steps, the CPU load was high, likely because the user wanted a program to finish executing after they disconnected. This also blocks shutdown
1. `inside inactivity window` indicates that, whilst the machine CPU load has dropped low enough to shutdown, it hasn't been long enough since this drop in load for the machine to shutdown
1. `shutting down machine` indicates that the machine is turning off 
