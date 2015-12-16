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
    license='BSD',
    author='Jason Bittel',
    author_email='jason.bittel@gmail.com',
    url='https://github.com/jbittel/django-mama-cas',
    download_url='https://pypi.python.org/pypi/django-mama-cas/',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['requests>=2.0.0,<3.0.0'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
    ],
    keywords=['auth', 'authentication', 'cas', 'django', 'single sign-on', 'sso'],
)
