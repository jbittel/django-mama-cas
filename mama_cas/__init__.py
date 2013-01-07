VERSION = (0, 3, 0, 'final', 0)

def get_version(version=None):
    """
    Derives a PEP386-compliant version number from VERSION.

    Adapted from the Django project's get_version() function.
    """
    if version is None:
        version = VERSION
    assert len(version) == 5
    assert version[3] in ('alpha', 'beta', 'rc', 'final')

    # Build the two parts of the version number:
    # main = X.Y.Z
    # sub = {a|b|c}N - for alpha, beta and rc releases

    main = '.'.join(str(x) for x in version[:3])

    sub = ''
    if version[3] != 'final':
        mapping = {'alpha': 'a', 'beta': 'b', 'rc': 'c'}
        sub = mapping[version[3]] + str(version[4])

    return main + sub
