# Silica
[![Build Status](https://travis-ci.com/leonardt/silica.svg?token=BftLM4kSr1QfgPspi6aF&branch=master)](https://travis-ci.com/leonardt/silica)
[![codecov](https://codecov.io/gh/leonardt/silica/branch/master/graph/badge.svg)](https://codecov.io/gh/leonardt/silica)
[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

Silica is a language embedded in Python that uses coroutines to describe
hardware finite state machines.

Requires Python 3.5+
# Setup
## Prerequisits
* Python 3
  Recommended portable installation method is using [miniconda](https://conda.io/miniconda.html)
* (Optional) graphviz
  For rendering control flow graphs

Install Python dependencies
```shell
pip install -r dev-requirements.txt
```
Install Silica as a local Python package
```shell
pip install -e .
```

Run the Test Suite
```shell
py.test --cov=silica --cov-report term-missing test
```

# Syntax
Extends [mantle](https://github.com/phanrahan/mantle) syntax with
```
S ::= ...
    | if ( E ) { S* } else { S* }
    | if ( E ) { S* }
    | while ( E ) { S* }
    | for ( Id in range(Num) { S* }  # TODO: Should we support more than ranges?
    | yield
    | yield from Id
```
