Changelog for Sequence
======================

.. towncrier release notes start

0.4.0 (2021-07-26)
------------------

New Features
````````````

- Added "plot" subcommand to sequence for plotting stratigraphic output
  from a netcdf file. (`#25 <https://github.com/sequence-dev/sequence/issues/25>`_)


Bug Fixes
`````````

- Fixed layer interpolation when plotting. (`#28 <https://github.com/sequence-dev/sequence/issues/28>`_)


Documentation Enhancements
``````````````````````````

- Updated README documentation. Added descriptions of the
  sequence.grid and sequence.output sections for the
  sequence.toml file, and added documentation for the plot
  subcommand (`#27 <https://github.com/sequence-dev/sequence/issues/27>`_)


Other Changes and Additions
```````````````````````````

- Changed to use GitHub Actions for continuous integration. (`#26 <https://github.com/sequence-dev/sequence/issues/26>`_)


0.3.0 (2020-08-11)
------------------

New Features
````````````

- Added more time-varying parameters to SubmarineDiffuser. (`#24 <https://github.com/sequence-dev/sequence/issues/24>`_)


Documentation Enhancements
``````````````````````````

- Improved documentation for time-varying parameters. (`#23 <https://github.com/sequence-dev/sequence/issues/23>`_)


0.2.0 (2020-07-30)
------------------

New Features
````````````

- Added support for toml-formatted input files and is now the default. (`#1 <https://github.com/sequence-dev/sequence/issues/1>`_)
- Added time varying parameters. (`#18 <https://github.com/sequence-dev/sequence/issues/18>`_)
- Allow subsidence to vary with time. (`#21 <https://github.com/sequence-dev/sequence/issues/21>`_)


Other Changes and Additions
```````````````````````````

- Fixed CI on Travis and AppVeyor. (`#18 <https://github.com/sequence-dev/sequence/issues/18>`_)
- Use readthedocs file to configure documentation building. (`#19 <https://github.com/sequence-dev/sequence/issues/19>`_)
- Changed to use landlab version 2 components. (`#20 <https://github.com/sequence-dev/sequence/issues/20>`_)
- Added lots of new tests, particularly for reading/writing configuration files. (`#21 <https://github.com/sequence-dev/sequence/issues/21>`_)


0.1.2 (2020-03-04)
------------------ 

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


0.1.1 (2018-08-24)
------------------ 
- Added versioneer for version management


0.1.0 (2018-08-24)
------------------ 

- Initial release

