#!/usr/bin/env python

from distutils.core import setup
import os

from mama_cas import __version__ as version


def read_file(filename):
    """
    Utility function to read a provided filename.
    """
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


packages = [
    'mama_cas',
    'mama_cas.management',
    'mama_cas.management.commands',
    'mama_cas.tests',
]

package_data = {
    '': ['LICENSE', 'README.rst'],
    'mama_cas': ['templates/mama_cas/*.html', 'templates/mama_cas/*.xml']
}

setup(
    name='django-mama-cas',
    version=version,
    description='A CAS server single sign-on application for Django',
    long_description=read_file('README.rst'),
    author='Jason Bittel',
    author_email='jason.bittel@gmail.com',
    url='https://github.com/jbittel/django-mama-cas',
    download_url='https://github.com/jbittel/django-mama-cas/downloads',
    package_dir={'mama_cas': 'mama_cas'},
    packages=packages,
    package_data=package_data,
    license='BSD',
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
    install_requires=['requests == 1.1.0'],
)
