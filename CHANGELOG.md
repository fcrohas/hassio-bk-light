# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-04

### Added
- Initial release
- Support for BK Light ACT1026 LED controller
- On/Off control
- Brightness adjustment (0-255)
- RGB color control
- 20 built-in effects
- Config flow for UI-based setup
- YAML configuration support (legacy)
- French translations
- HACS compatibility

### Features
- Local polling integration
- TCP/IP communication on port 5577
- Automatic device discovery option
- Device info display
- Entity naming
- Options flow for reconfiguration

### Known Issues
- Color temperature control not yet implemented (device may not support it)
- Effect speed control is fixed at 50% (will be configurable in future release)
