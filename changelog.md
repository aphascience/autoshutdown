# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 15/08/2024

### Changed

- Use abs path of `version.properties`

## [1.0.4] - 15/08/2024

### Changed

- Updated pyinstaller version to 6.10.0 in the hope that it uses a stable version of openssl.

### Added

- version number to to first line of the log, indicating the autoshutdown has started: i.e. `Starting auto-off routine: machine will shutdown after 30 minutes of inactivity` -> `Starting autoshutdown_v1.0.4: machine will shutdown after 30 minutes of inactivity`

## [1.0.3] - 09/07/2024 (open sourcing)

### Changed

- All references to SCE in readme and folder / file names removed
- Removed SCE specific installation instructions from the readme
- Added more details to and generally improved the readme

## [1.0.2] - 28/05/2024 

### Changed 

- The distribution folder has changed name from `sceautoshutdown_dist1.0.1` to `sceautoshutdown_v1.0.1`.

## [1.0.1] - 23/05/2024 

### Fixed 

- `make` was looking for changes to `sceautoshutdown_dist/` on the clean target. This wasn't working because new folder structure has a version number on the distribution folder. This is fixed now: `sceautoshutdown_dist*/`.

## [1.0.0] - 22/05/2024 

### Added

- First major release to SCE users

## [0.1.0]

### Added

- Initial dump of code, featuring working versions of `activate_cron.py`, `auto_off.py`, install scripts, Makefile etc...
- This `changelog.md` for tracking versions.
- A feature to ensure that `activate_cron` is run with `sudo` and exit gracefully right at the start rather if not, rather than crashing out down the line when root privilages needed.
