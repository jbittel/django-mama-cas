from distutils.core import setup
import os

from mama_cas import __version__ as version


def split_relative_path(path):
    """
    Given a path, return the path as a string with the
    first path component removed (e.g. 'foo/bar/baz' would
    be returned as 'bar/baz').
    """
    parts = []
    while True:
        head, tail = os.path.split(path)
        if head == path:
            if path:
                parts.append(path)
            break
        parts.append(tail)
        path = head
    parts.reverse()
    if len(parts) > 1:
        return os.path.join(*parts[1:])
    else:
        return ''


def get_readme(filename):
    """
    Utility function to print the README file, used for the long_description
    setup argument below.
    """
    return open(os.path.join(os.path.dirname(__file__), filename)).read()


packages, package_data = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

# Collect the lists of packages and package files, starting
# from the base project directory (adapted from the Django setup script)
for dirpath, dirnames, filenames in os.walk('mama_cas'):
    # Collect packages
    if '__init__.py' in filenames:
        pkg_path = os.path.normpath(dirpath)
        pkg = pkg_path.replace(os.sep, '.')
        if os.altsep:
            pkg = pkg.replace(os.altsep, '.')
        packages.append(pkg)
    # Collect ancillary package files
    elif filenames:
        relative_path = split_relative_path(dirpath)
        for f in filenames:
            package_data.append(os.path.join(relative_path, f))

setup(
    name='django-mama-cas',
    version=version,
    description='A CAS server single sign-on application for Django',
    long_description=get_readme('README'),
    author='Jason Bittel',
    author_email='jason.bittel@gmail.com',
    url='http://github.com/jbittel/django-mama-cas',
    download_url='http://github.com/jbittel/django-mama-cas/downloads',
    package_dir={'mama_cas': 'mama_cas'},
    packages=packages,
    package_data={'mama_cas': package_data},
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Programming Language :: Python',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords=['django', 'cas', 'single sign-on', 'authentication', 'auth'],
    install_requires=['requests == 1.0.4'],
)
