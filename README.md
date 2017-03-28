# Silica
[![Build Status](https://travis-ci.org/leonardt/silica.svg?branch=master)](https://travis-ci.org/leonardt/silica)
[![codecov](https://codecov.io/gh/leonardt/silica/branch/master/graph/badge.svg)](https://codecov.io/gh/leonardt/silica)

A language embedded in Python for building Finite State Machines in hardware.

Requires Python 3.5+

# Development Setup
```shell
pip install -r requirements.txt
pip install pytest # Testing infrastructure
pip install -e .   # Install local working copy
```

###  Optional requirements
* graphviz (`pip install graphviz`) to render control flow graphs

## Running the Test Suite
```shell
py.test --cov=silica --cov-report term-missing test
```
