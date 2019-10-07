from setuptools import find_packages, setup, Command
import stat
import os
from shutil import rmtree
import sys

# Package meta-data.
NAME = 'unmock'
DESCRIPTION = 'The Unmock Python clent'
URL = 'https://www.unmock.io/'
EMAIL = 'dev@meeshkan.com'
AUTHOR = 'Meeshkan Dev Team'
REQUIRES_PYTHON = '>=2.7.0,!=3.0*,!=3.1*,!=3.2*,!=3.3*'
SRC_DIR = 'unmock'  # Relative location wrt setup.py

# Required packages.
REQUIRED = ["requests", "six"]

DEV = ["twine", "wheel", "pytest", "coverage"]

# List of support packages needed based on python version used.
# Tuple format: (version tuple, package to install)
# The major-minor version should be the version when a package was introduced, so any older version would use the
#   support package.
SUPPORT = [
    ((3, 3), "mock")  # unittest.mock was added in Python 3.3
]
for (ver, pkg) in SUPPORT:
  if sys.version_info < ver:
    REQUIRED.append(pkg)

# Optional packages
EXTRAS = {'dev': DEV}

# Entry point (relative to setup.py)
ENTRY_POINTS = []

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
with open(os.path.join(here, 'README.md')) as f:
  long_description = '\n' + f.read()

# Load the package's __version__.py module as a dictionary.
about = dict()
with open(os.path.join(here, SRC_DIR, '__version__.py')) as f:
  exec(f.read(), about)


class SetupCommand(Command):
  """Base class for setup.py commands with no arguments"""
  user_options = []

  def initialize_options(self):
    pass

  def finalize_options(self):
    pass

  @staticmethod
  def status(s):
    """Prints things in bold."""
    print('\n\033[1m{0}\033[0m'.format(s))


class PushGitTagCommand(SetupCommand):
  """Supports setup.py tags"""
  description = "Pushes a git tag"

  def run(self):
    self.status("Pushing git tags...")
    os.system("git tag v{about}".format(about=about['__version__']))
    os.system("git push --tags")

    sys.exit()


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='Apache 2.0',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Framework :: Pytest',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing :: Mocking'
    ],
    entry_points={'pytest11': ['unmock = unmock.pytest.plugin']},
    cmdclass={'tags': PushGitTagCommand}
)
