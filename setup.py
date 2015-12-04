# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='fangzi',
    version='0.1.0',
    keywords=u'fangzi',
    description=u'Python-Dynamic-FunctionCheck-Tools',
    long_description=open("README.md").read(),
    license='MIT License',

    author='lwxiang',
    author_email='lwxiang1994@gmail.com',

    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    install_requires=map(lambda x: x.replace('==', '>='), open("requirement.txt").readlines()),
)
