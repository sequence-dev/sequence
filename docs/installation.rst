.. _basic_install:

Installation
============

.. important::

  The following commands will install *sequence* into your current environment. Although
  not necessary, we **highly recommend** you install sequence into its own
  :ref:`virtual environment <virtual_environments>`.

.. start-install-release

In order to use *sequence* you will first need Python. While not
necessary, we recommend using the
`Anaconda Python distribution <https://www.anaconda.com/distribution/>`_
as it provides a large number of third-party packages useful for
scientific computing.

To install *Sequence*, simply run the following in your terminal of choice:

.. tab:: mamba

  .. code-block:: bash

    conda install mamba -c conda-forge
    mamba install sequence-model -c conda-forge

.. tab:: conda

  .. code-block:: bash

    conda install sequence-model -c conda-forge

.. tab:: pip

  .. code-block:: bash

    pip install sequence-model

.. end-install-release

If you would like the very latest development version of *sequence* or want to modify
or contribute code to the *sequence* project, you will need to do a
:ref:`developer installation <install>` of *sequence* from source.
