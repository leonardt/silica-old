# Silica
[![Build Status](https://travis-ci.org/leonardt/silica.svg?branch=master)](https://travis-ci.org/leonardt/silica)
[![codecov](https://codecov.io/gh/leonardt/silica/branch/master/graph/badge.svg)](https://codecov.io/gh/leonardt/silica)

A language embedded in Python for building Finite State Machines in hardware.

Requires Python 3.5+

# Development Setup
```shell
sudo apt install python3  # Ubuntu 16.04
brew install python3      # MacOS/Homebrew
```

[virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/index.html)
is useful tool for managing project specific Python environments.  Setup an
environment with a Python version 3.5 or greater.
```shell
pip install virtualenvwrapper
mkvirtualenv --python=python3 silica
```

Install package dependencies
```shell
pip install -r requirements.txt
```

Install a local working copy of Silica
```shell
pip install -e .
```

###  Optional requirements
* graphviz (`pip install graphviz`) to render control flow graphs

## Running the Test Suite
```shell
py.test --cov=silica --cov-report term-missing test
```
