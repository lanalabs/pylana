# How to contribute

Thanks for your interest in PyLana. This guide is a stub right now and will extend over time.

## Setting up the environment

We provide a conda `environment-dev.yaml` to get started.

## Testing

For testing please see the [test documentation](tests/README.md). 

## Coding conventions

* for coding style we try follow the [PEP 8 - Style Guide for Python Code](https://www.python.org/dev/peps/pep-0008/)
* for doc strings we orient at the [Google style guide](http://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
* type annotate your functions
* only use frequently used http verbs (get, put, post, patch, delete) for general api methods



## Packaging

For testing our packages, we have a test-pypi project. When installing from test pypi, don't forget to reference the normal pypi as an extra index url

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pylana
``` 
 
 Otherwise the installation of dependencies will likely fail.  

