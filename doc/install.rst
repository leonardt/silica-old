.. install:

Installing silica
===================

External Dependencies
---------------------
* | Python 3
  | Recommended lightweight, portable installation method is with 
    `miniconda <https://conda.io/miniconda.html>`_.
* | [Optional] `graphviz <http://www.graphviz.org/>`_
  | For developing silica internals, graphviz is used to render
    control flow graphs

Installation
------------

.. code-block:: shell

    $ pip install -r requirements.txt
    $ pip install .

Developer Setup
---------------
Install packages used for testing and debugging

.. code-block:: shell

    $ pip install -r dev-requirements.txt

Install a local working copy of Silica as a *symbolic* Python package

.. code-block:: shell

    $ pip install -e .

Run the test suite to verify the setup process

.. code-block:: shell

    $ py.test --cov=silica --cov-report term-missing test
