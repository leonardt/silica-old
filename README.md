[![Build Status](https://travis-ci.com/leonardt/silica.svg?token=BftLM4kSr1QfgPspi6aF&branch=master)](https://travis-ci.com/leonardt/silica)
# Silica
A language embedded in Python for building Finite State Machines in hardware.

Requires Python 3.5+

# Development Setup
```
pip install -r requirements.txt
pip install pytest
export PYTHONPATH=`pwd`:$PYTHONPATH
pytest  # Check tests pass
```
## Optional requirements
* graphviz (`pip install graphviz`) to render control flow graphs
