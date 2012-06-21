from distutils.core import setup
import os


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

packages, package_data = [], []
root_dir = os.path.dirname(__file__)
if root_dir:
    os.chdir(root_dir)

# Collect the lists of packages and package files, starting
# from the base project directory
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
    name = 'django-mama-cas',
    version = '0.1',
    description = 'A CAS server single sign-on application for Django',
    author = 'Jason Bittel',
    author_email = 'jason.bittel@gmail.com',
    url = 'http://github.com/jbittel/django-mama-cas',
    package_dir = { 'mama_cas': 'mama_cas' },
    packages = packages,
    package_data = { 'mama_cas': package_data },
)
