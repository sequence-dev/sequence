# Release Notes

```{towncrier-draft-entries} Not yet released
```

<!-- towncrier-draft-entries:: Not yet released -->

<!-- towncrier release notes start -->

## 0.6.0 (2023-12-20)


### 🍰 New Features

- Added the ability for a user to control both what processes are run in a
  *Sequence* simulation and the order with which those processes are run. [#62](https://github.com/sequence-dev/sequence/issues/62)
- Changed all components to only update the current amount of subsidence and
  deposited sediment but not to update secondary fields like the topographic
  elevation. This removes the dependence of these secondary fields on
  component ordering and ensures these secondary fields are updated once, and only
  once, with each time step. [#67](https://github.com/sequence-dev/sequence/issues/67)
- Added a {meth}`~sequence.SequenceModelGrid.get_profile` method to {class}`~sequence.SequenceModelGrid` that is a convenience
  function to return a field just along the middle row of nodes (i.e. along the
  profile). [#67](https://github.com/sequence-dev/sequence/issues/67)
- Improved the logging of *Sequence*. *Sequence* now logs time spent running
  each component, and the options available for the plot command. From the
  command line, users are able to control the detail of the log messages through
  the `--verbose` and `--silent` options. [#68](https://github.com/sequence-dev/sequence/issues/68)
- Changed the {class}`~sequence.sediment_flexure.SedimentFlexure` component so
  that it is no longer dependent on the ordering of components. It has been
  simplified so that it now takes sediment loading as its only input field. [#71](https://github.com/sequence-dev/sequence/issues/71)
- Added a new component, {class}`~sequence.sediment_flexure.WaterFlexure`, that
  calculates deflections based on changes in water loading. [#72](https://github.com/sequence-dev/sequence/issues/72)
- Added a quasi-2d mode for *Sequence* that keeps track of multiple cross-shore
  rows. [#78](https://github.com/sequence-dev/sequence/issues/78)


### 🛠️ Bug Fixes

- Fixed a bug that caused a `FieldError` when running *Sequence* without the
  subsidence component enabled. [#64](https://github.com/sequence-dev/sequence/issues/64)
- Fixed a bug where the topographic elevations were not being updated correctly after the
  components were time stepped. [#67](https://github.com/sequence-dev/sequence/issues/67)
- Fixed a bug that incorrectly updated the profile elevations. Elevations were
  being updated before the new layer was added rather than after.
  Among other things, this caused the submarine diffuser component to use
  incorrect diffusion coeffients. [#73](https://github.com/sequence-dev/sequence/issues/73)


### 📖 Documentation Enhancements

- Updated the *sequence* documentation to include a page for
  [example notebooks](https://sequence.readthedocs.io/en/develop/notebooks.html). [#58](https://github.com/sequence-dev/sequence/issues/58)
- Reorganized and cleaned up the documentation and switched to the [furo](https://pradyunsg.me/furo/) theme. [#59](https://github.com/sequence-dev/sequence/issues/59)
- Updated the description of *sequence.toml* input file in the user guide. [#65](https://github.com/sequence-dev/sequence/issues/65)
- Updated the documentation to now include an unreleased section of the release
  notes that includes changes since the latest release. [#69](https://github.com/sequence-dev/sequence/issues/69)
- Converted the documentation files from reStructuredText to MyST-flavored
  markdown format. [#76](https://github.com/sequence-dev/sequence/issues/76)
- Reorganize the docs to follow the [Diátaxis](https://diataxis.fr/)
  Grand Unified Theory of Documentation. [#77](https://github.com/sequence-dev/sequence/issues/77)


### 🔩 Other Changes and Additions

- Set up [nox](https://nox.thea.codes) to automate testing and routine package
  maintenance. [#60](https://github.com/sequence-dev/sequence/issues/60)
- Added additional linters to the pre-commit hooks and removed the newly-found lint. [#61](https://github.com/sequence-dev/sequence/issues/61)
- Significantly simplified the *grid* section of the input file. [#62](https://github.com/sequence-dev/sequence/issues/62)
- Added unit tests to test *Sequence* runs for different combinations and ordering of components. [#64](https://github.com/sequence-dev/sequence/issues/64)
- Enforce the existence of docstrings for all public function, classes, etc. and
  ensure those docstrings adhere to the *numpy* docstring conventions. [#65](https://github.com/sequence-dev/sequence/issues/65)
- Added type hints to the entire code base and a *mypy* hook to the *pre-commit* linters to identify potential typing issues. [#66](https://github.com/sequence-dev/sequence/issues/66)
- Added tests for the compaction, flexure, and subsidence components. [#67](https://github.com/sequence-dev/sequence/issues/67)
- Fixed an issue with building the docs on *readthedocs*. [#70](https://github.com/sequence-dev/sequence/issues/70)
- Updated the repository continuous integration by adding new linters for the
  notebooks, and add testing for Python 3.11. [#74](https://github.com/sequence-dev/sequence/issues/74)
- Added support for Python 3.12 and dropped support for Python version older
  than 3.10. [#79](https://github.com/sequence-dev/sequence/issues/79)
- Updated *Sequence* annotations to python 3.10+. [#82](https://github.com/sequence-dev/sequence/issues/82)
- Renamed the unit test files so that they all have a ``_test`` suffix rather
  than a ``test_`` prefix. [#90](https://github.com/sequence-dev/sequence/issues/90)

## 0.5.1 (2022-06-30)

### 🛠️ Bug Fixes

- Fixed a bug where x_of_shore and x_of_shelf_edge were being incorrectly
  recorded (but correctly calculated). ([#57](https://github.com/sequence-dev/sequence/issues/57))

## 0.5.0 (2022-06-29)

### 📚 New Tutorial Notebooks

- Added a tutorial notebook that demonstrates the use of the new `Sequence`
  class and how one can build, run and dynamically modify a new *sequence*
  model from a series of process components. ([#51](https://github.com/sequence-dev/sequence/issues/51))

### 🍰 New Features

- Added several new setters to `SedimentFlexure` that allows a user to
  dynamically change paramters while the model is running. These include:
  sediment densities (sand and mud), and water density. ([#45](https://github.com/sequence-dev/sequence/issues/45))
- Added *water_density* as an input parameter to `SedimentFlexure`. ([#45](https://github.com/sequence-dev/sequence/issues/45))
- Added a new function, `plot_grid`, that plots the output of a *sequence*
  model from Python. This serves as the programmatic equivalent of the
  `sequence plot` command-line program. ([#50](https://github.com/sequence-dev/sequence/issues/50))
- Added a new module `sequence.processes` that holds all processes that can
  be used to construct a new *sequence* model. ([#50](https://github.com/sequence-dev/sequence/issues/50))
- Added `Sequence` class that allows a user to construct and run *sequence*
  models within a Python environment and dynamically change input variables. ([#50](https://github.com/sequence-dev/sequence/issues/50))
- Added a `SequenceModelGrid` class, based on a *landlab* `RasterModelGrid`,
  that creates a grid that can be used for creating new *sequence* models. ([#50](https://github.com/sequence-dev/sequence/issues/50))
- Added a new method, *run*, to *Sequence* that allows a user to run the model
  until a given time and with a given time step. ([#54](https://github.com/sequence-dev/sequence/issues/54))

### 🛠️ Bug Fixes

- Fixed a bug where the sea floor was not plotted in some situations. ([#46](https://github.com/sequence-dev/sequence/issues/46))
- Fixed a bug where the `Compact` component would fail to run because
  porosity was not being tracked within layers. ([#51](https://github.com/sequence-dev/sequence/issues/51))

### 🔩 Other Changes and Additions

- Updated the `SedimentFlexure` component to be compatible with the latest
  version of *landlab*. ([#45](https://github.com/sequence-dev/sequence/issues/45))
- Added unit tests for the `SedimentFlexure` component. ([#45](https://github.com/sequence-dev/sequence/issues/45))
- Upgraded Python syntax to 3.8 and above. ([#47](https://github.com/sequence-dev/sequence/issues/47))
- Setup of pre-commit for the project that runs *black*, *flake8*, and
  *pyupgrade* (for Python 3.8+). ([#48](https://github.com/sequence-dev/sequence/issues/48))
- Added GitHub Actions workflows for releasing Sequence to PyPI and TestPyPI
  (for pre-releases). This allows users to run `pip install sequence` to get
  the latest release. ([#49](https://github.com/sequence-dev/sequence/issues/49))
- Updated the pre-commit hooks to ensure notebooks are clean and styled
  correctly. ([#51](https://github.com/sequence-dev/sequence/issues/51))
- Added a GitHub Actions workflow that tests the *sequence* notebooks. The
  notebooks are simply executed to ensure they run, not to validate any output. ([#52](https://github.com/sequence-dev/sequence/issues/52))
- Added a citation file that users of *sequence* can use to cite the software. ([#53](https://github.com/sequence-dev/sequence/issues/53))

## 0.4.1 (2022-04-12)

### 🍰 New Features

- Added `--silent` option to supress status messages and the progress bar. ([#30](https://github.com/sequence-dev/sequence/issues/30))

### 🛠️ Bug Fixes

- Fixed a bug where, instead of writing the current model time, *Sequence* was
  writing the model time step number to the output file as the *time* variable. ([#34](https://github.com/sequence-dev/sequence/issues/34))
- Fixed a bug that incorrectly determined the shore and shelf edge at startigraphic layers
  when writing *netCDF* output. This was only an issue when *Sequence* had averaged buried layers. ([#37](https://github.com/sequence-dev/sequence/issues/37))
- Changed the defaults generated by `sequence setup` to create a set of input
  files that generate output that can be plotted by `sequence plot`. ([#39](https://github.com/sequence-dev/sequence/issues/39))
- Fixed a bug that caused the `sequence plot` command to fail if the entire profile
  was above sea level. ([#40](https://github.com/sequence-dev/sequence/issues/40))

### 🔩 Other Changes and Additions

- Fixed continuous integration tests by removing lint, limit numpy version. ([#30](https://github.com/sequence-dev/sequence/issues/30))
- Modified requirements file to exclude numpy versions that caused a core dump when running Sequence with the compaction component. ([#31](https://github.com/sequence-dev/sequence/issues/31))
- Setup Sequence to use towncrier to manage the changelog. ([#32](https://github.com/sequence-dev/sequence/issues/32))
- Setup [towncrier](https://github.com/twisted/towncrier) to manage the chagnelog. ([#33](https://github.com/sequence-dev/sequence/issues/33))
- The `sequence plot` command now prints a better error message if the
  *netCDF* output file being plotted is missing a required variable. ([#39](https://github.com/sequence-dev/sequence/issues/39))
- Added Python 3.10 to the continuous integration tests. ([#42](https://github.com/sequence-dev/sequence/issues/42))

## 0.4.0 (2021-07-26)

### 🍰 New Features

- Added "plot" subcommand to sequence for plotting stratigraphic output
  from a netcdf file. ([#25](https://github.com/sequence-dev/sequence/issues/25))

### 🛠️ Bug Fixes

- Fixed layer interpolation when plotting. ([#28](https://github.com/sequence-dev/sequence/issues/28))

### 📖 Documentation Enhancements

- Updated README documentation. Added descriptions of the
  sequence.grid and sequence.output sections for the
  sequence.toml file, and added documentation for the plot
  subcommand ([#27](https://github.com/sequence-dev/sequence/issues/27))

### 🔩 Other Changes and Additions

- Changed to use GitHub Actions for continuous integration. ([#26](https://github.com/sequence-dev/sequence/issues/26))

## 0.3.0 (2020-08-11)

### 🍰 New Features

- Added more time-varying parameters to SubmarineDiffuser. ([#24](https://github.com/sequence-dev/sequence/issues/24))

### 📖 Documentation Enhancements

- Improved documentation for time-varying parameters. ([#23](https://github.com/sequence-dev/sequence/issues/23))

## 0.2.0 (2020-07-30)

### 🍰 New Features

- Added support for toml-formatted input files and is now the default. ([#1](https://github.com/sequence-dev/sequence/issues/1))
- Added time varying parameters. ([#18](https://github.com/sequence-dev/sequence/issues/18))
- Allow subsidence to vary with time. ([#21](https://github.com/sequence-dev/sequence/issues/21))

### 🔩 Other Changes and Additions

- Fixed CI on Travis and AppVeyor. ([#18](https://github.com/sequence-dev/sequence/issues/18))
- Use readthedocs file to configure documentation building. ([#19](https://github.com/sequence-dev/sequence/issues/19))
- Changed to use landlab version 2 components. ([#20](https://github.com/sequence-dev/sequence/issues/20))
- Added lots of new tests, particularly for reading/writing configuration files. ([#21](https://github.com/sequence-dev/sequence/issues/21))

## 0.1.2 (2020-03-04)

- Added sediment compaction
- Updated installation docs (#17)
- Update sequence documentation (#16)
- Added AppVeyor CI for Windows testing (#15)
- Fixed failing shelf edge tests (#14)
- Added examples to sequence cli help message
- Added Python 3.8 support and testing; remove Python 2.7
- Add setup/show/run subcommands to the sequence CLI
- Updated for landlab v2 pre-release version
- Added hemipelagic parameter to sediments section of configuration file
- Bug fixes
- Added ability to read a user-supplied sea level file
- Enhance CI testing
- Added ability to write output at intervals (#11)
- Write a subset of variable fields to netcdf output files

## 0.1.1 (2018-08-24)

- Added versioneer for version management

## 0.1.0 (2018-08-24)

- Initial release
