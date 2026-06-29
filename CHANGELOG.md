# Changelog

All notable changes to the WebPulse project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0-sprint1] - 2026-06-29

### Added
* **Exceptions Module (`webpulse.core.exceptions`)**: Implemented base exceptions hierarchy: `WebPulseException`, `ConfigurationException`, `SecurityException`, `PluginException`.
* **Pydantic Validation Schemas (`webpulse.core.config`)**: Implemented Pydantic v2 schemas for `core`, `network`, `crawler`, `auth`, `modules`, and `reporting` config parameters.
* **Hierarchical Config Management**: Created `ConfigManager` to load settings from YAML/JSON/TOML, merge CLI variables, apply profile presets (`fast`, `default`, `full`), and substitute env variable credentials dynamically.
* **Thread-Safe Dependency Locator (`webpulse.core.di`)**: Built the `Container` service locator class utilizing a thread-safety re-entrant locking model.
* **Structured CLI Logging Formatter (`webpulse.utils.logging`)**: Implemented console logs formatting that respects `NO_COLOR` spec directives and dynamically handles TTY checks.
* **Manual Verification Utility (`examples/load_config.py`)**: Setup script to demonstrate log outputs and config load merging.

### Modified
* **`pyproject.toml`**: Moved Ruff linter configuration properties under `[tool.ruff.lint]` and added ignore patterns for exception class naming conventions (`N818`) and tests magic numbers (`PLR2004`, `PTH123`, `SIM105`).

### Fixed
* **Profile Type Constraint**: Constrained config `profile` parameter to `Literal["fast", "default", "full"]` to enforce type check validations.
* **Deep Dictionary Cloning**: Upgraded config environment variables merger to use `copy.deepcopy` to prevent shared state mutations.
* **Type Casting**: Swapped out DI container `# type: ignore` annotations for strict `typing.cast` bindings.
