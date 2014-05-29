#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

from mama_cas import __version__ as version


with open('README.rst') as f:
    readme = f.read()

setup(
    name='django-mama-cas',
    version=version,
    description='A Django Central Authentication Service (CAS) single sign-on server',
    long_description=readme,
    author='Jason Bittel',
    author_email='jason.bittel@gmail.com',
    url='https://github.com/jbittel/django-mama-cas',
    download_url='https://github.com/jbittel/django-mama-cas/downloads',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['django', 'cas', 'single sign-on', 'authentication', 'auth'],
    install_requires=['requests>=2.0.0,<3.0.0'],
)
