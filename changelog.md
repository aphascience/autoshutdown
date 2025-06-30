# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-06-30

No longer using PyInstaller packaging tool. Instead relying on user's Python. Users simply download the source code in this repo, keep the file structure as is and run the shell script, `activate.sh`. 

### Changed

- `PyInstaller` dependency is removed. We now rely on the user's python interpreter  instead.
- `activate_cron.py` and `auto_off.py` are run within automatically created virtual environments wrapped in the shell scripts `activate.sh` and `auto_off.sh`.

### Added 
- `activate.sh`, `auto_off.sh` and `unit_tests.sh` used to run `activate_cron.py`, `auto_off.py` and `unit_tests.py` within dedicated python virtual environments. 
- New `dist/` directory is made the home of `auto_off.py` and `auto_off.sh`. 

### Removed
- `autoshutdown.spec` - this is no longer needed as it was a `PyInstaller` dependency.
- `build.sh` - was used to package application with `PyInstaller` so no longer needed.
- `Makefile` - dependency on `make` is removed as no package building required.

## [1.1.1] - 2025-03-13

### Changed

- Report the most recent recorded loadavg in the logs alongside "system busy", "inside inactivity window" & "shutting down machine" messages.

## [1.0.5] - 2024-08-15

### Changed

- Use abs path of `version.properties`

## [1.0.4] - 2024-08-15

### Changed

- Updated pyinstaller version to 6.10.0 in the hope that it uses a stable version of openssl.

### Added

- version number to to first line of the log, indicating the autoshutdown has started: i.e. `Starting auto-off routine: machine will shutdown after 30 minutes of inactivity` -> `Starting autoshutdown_v1.0.4: machine will shutdown after 30 minutes of inactivity`

## [1.0.3] - 2024-07-09 (open sourcing)

### Changed

- All references to SCE in readme and folder / file names removed
- Removed SCE specific installation instructions from the readme
- Added more details to and generally improved the readme

## [1.0.2] - 2024-05-28 

### Changed 

- The distribution folder has changed name from `sceautoshutdown_dist1.0.1` to `sceautoshutdown_v1.0.1`.

## [1.0.1] - 2024-05-23 

### Fixed 

- `make` was looking for changes to `sceautoshutdown_dist/` on the clean target. This wasn't working because new folder structure has a version number on the distribution folder. This is fixed now: `sceautoshutdown_dist*/`.

## [1.0.0] - 2024-05-22 

### Added

- First major release to SCE users

## [0.1.0]

### Added

- Initial dump of code, featuring working versions of `activate_cron.py`, `auto_off.py`, install scripts, Makefile etc...
- This `changelog.md` for tracking versions.
- A feature to ensure that `activate_cron` is run with `sudo` and exit gracefully right at the start rather if not, rather than crashing out down the line when root privilages needed.
