[![Build Status](https://travis-ci.com/leonardt/silica.svg?token=BftLM4kSr1QfgPspi6aF&branch=master)](https://travis-ci.com/leonardt/silica)
[![codecov](https://codecov.io/gh/leonardt/silica/branch/master/graph/badge.svg)](https://codecov.io/gh/leonardt/silica)

# Silica
A language embedded in Python for building Finite State Machines in hardware.

Requires Python 3.5+

# Development Setup
```shell
pip3 install -r requirements.txt
pip3 install pytest # Testing infrastructure
pip3 install -e .   # Install local working copy
```

###  Optional requirements
* graphviz (`pip install graphviz`) to render control flow graphs

## Running the Test Suite
```shell
py.test --cov=silica --cov-report term-missing test
```
