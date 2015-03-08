#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='SnapWrap',
    version='0.1',
    description="Wrapper for Snapchat's API!",
    long_description="This is an API wrapper for Snapchat's unofficial and undocumented API.",
    author='Robert',
    url=' https://github.com/Rob--/SnapWrap',
    packages=['SnapWrap', 'SnapWrap.Client'],
    install_requires=[
        'schedule>=0.3.1',
        'requests>=2.5.1',
        'Pillow>=2.7.0'
    ],
    license='The MIT License (MIT) - see LICENSE'
)