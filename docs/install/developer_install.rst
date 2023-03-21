.. _install:

=================
Developer Install
=================

.. important::

  The following commands will install *sequence* into your current environment. Although
  not necessary, we **highly recommend** you install sequence into its own
  :ref:`virtual environment <virtual_environments>`.


If you will be modifying code or contributing new code to *sequence*, you will first
need to get *sequence*'s source code and then install *sequence* from that code.

Source Install
--------------

.. start-install-source

*sequence* is actively being developed on GitHub, where the code is freely available.
If you would like to modify or contribute code, you can either clone our
repository

.. code-block:: bash

   git clone git://github.com/sequence-dev/sequence.git

or download a `zip file <https://github.com/sequence-dev/sequence/archive/refs/heads/develop.zip>`_:

.. code-block:: bash

   curl -OL https://github.com/sequence-dev/sequence/archive/refs/heads/develop.zip

Once you have a copy of the source code, you can install it into your current
Python environment,

.. tab:: mamba

  .. code-block:: bash

     cd sequence
     mamba install --file=requirements.in
     pip install -e .

.. tab:: conda

  .. code-block:: bash

     cd sequence
     conda install --file=requirements.in
     pip install -e .

.. tab:: pip

  .. code-block:: bash

     cd sequence
     pip install -e .

.. end-install-source

Developer Tools
---------------

Once you start developing with *sequence*, we recommend that you use `nox`_  to
automate common tasks such as, for example, running the tests, building the docs, and
finding lint.

.. _nox: https://nox.thea.codes/en/stable/

.. code-block:: bash

  pip install nox

The following list show how to use `nox`_ for some of the more common tasks:

* Run the tests:

  .. code-block:: bash

     nox -s test
* Run the tests on the notebooks:

  .. code-block:: bash

     nox -s test-notebooks
* Build the docs:

  .. code-block:: bash

     nox -s build-docs
* Run the linters:

  .. code-block:: bash

     nox -s lint
* To get a complete list of the available targets:

  .. code-block:: bash

     nox -l
