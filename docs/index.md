```{image} _static/sequence-logo-light.svg
:align: center
:alt: Sequence
:class: only-light
:width: 50%
:target: https://sequence.readthedocs.org/
```

```{image} _static/sequence-logo-dark.svg
:align: center
:alt: Sequence
:class: only-dark
:width: 50%
:target: https://sequence.readthedocs.org/
```

```{include} ../README.md
:start-after: "<!-- start-abstract -->"
:end-before: "<!-- end-abstract -->"
```

```{image} _static/sequence.png
:align: center
:alt: Sequence
:scale: 50%
:target: https://sequence.readthedocs.org/
```

# Installing Sequence

If you are new to *Sequence*, you can install it following the directions in
our [Basic Installation Guide](basic-install) but, in brief, it should be

````{tab} conda
```bash
conda install sequence-model -c conda-forge
```
````

````{tab} pip
```bash
pip install sequence-model
```
````

If you would like to modify the source code or contribute to the project,
you should follow our [Developer Installation Guide](source-install).


# Running Sequence

Visit the [Tutorials Section](tutorials-section) to get started with some
simple examples.

```{toctree}
:caption: Tutorials
:hidden: true
:maxdepth: 2

Command line <tutorials/cli/index>
Python <tutorials/notebooks/index>
```

```{toctree}
:caption: How-to guides
:hidden: true
:maxdepth: 2

Install <how_to_guides/install/index>
Create a Virtual Environment <how_to_guides/environments>
```

```{toctree}
:caption: Reference
:hidden: true
:maxdepth: 2

reference/cli/index
reference/api/index
```

<!--
```{toctree}
:caption: Getting Started
:hidden: true
:maxdepth: 2

installation
user_guide/index
notebooks/index
```

```{toctree}
:caption: Contributing
:hidden: true
:maxdepth: 2

install/index
api/index
```
-->

```{toctree}
:caption: About
:hidden: true
:maxdepth: 2

about/changelog
about/authors
about/contributing
License <about/license>
```

```{toctree}
:caption: Project Links
:hidden: true
:maxdepth: 2

GitHub <https://github.com/sequence-dev/sequence>
PyPI <https://pypi.org/project/sequence-model>
```
