import io
import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

DESCRIPTION = "Python API for LANA Process Mining"

try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


setup(name='pylana',
      version='0.2.1',
      description="Python API for LANA Process Mining",
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/lanalabs/pylana',
      author='Lana Labs GmbH',
      author_email='support@lanalabs.com',
      license='Apache2',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Programming Language :: Python :: 3'
      ],
      install_requires=[
          'requests',
          'pandas',
      ],
      packages=find_packages(),
)
