# Silica
[![Build Status](https://travis-ci.com/leonardt/silica.svg?token=BftLM4kSr1QfgPspi6aF&branch=master)](https://travis-ci.com/leonardt/silica)
[![codecov](https://codecov.io/gh/leonardt/silica/branch/master/graph/badge.svg)](https://codecov.io/gh/leonardt/silica)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

Silica is a language embedded in Python for constructing finite state machines
in digital hardware.

Requires Python 3.5+
# Setup
## Prerequisites
* Python 3  
  Recommended portable installation method is using [miniconda](https://conda.io/miniconda.html)
* (Optional) [graphviz](http://www.graphviz.org/)  
  For rendering control flow graphs
  
## Installation
```shell
pip install -r requirements.txt
python setup.py install
```

## Developer Setup
Install packages used for testing and debugging
```shell
pip install -r dev-requirements.txt
```
Install a local working copy of Silica as a *symbolic* Python package
```shell
pip install -e .
```

Run the test suite
```shell
py.test --cov=silica --cov-report term-missing test
```
