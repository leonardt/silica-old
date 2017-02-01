[![Build Status](https://travis-ci.com/leonardt/fsm_dsl.svg?token=BftLM4kSr1QfgPspi6aF&branch=master)](https://travis-ci.com/leonardt/fsm_dsl)

Requires Python 3.6

# Development Setup
```
pip install -r requirements.txt
pip install pytest
export PYTHONPATH=`pwd`:$PYTHONPATH
pytest  # Check tests pass
```
## Optional requirements
* graphviz (`pip install graphviz`) to render control flow graphs
