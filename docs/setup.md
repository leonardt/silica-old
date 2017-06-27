# Setup
Requires Python 3.5+
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
