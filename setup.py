import os
import sys

from setuptools import setup
from setuptools.command.install import install


VERSION = '0.3.4'


class VerifyVersionCommand(install):
    """Custom command to verify that the git tag matches our version"""
    description = 'verify that the git tag matches our version'

    def run(self):
        tag = os.getenv('CIRCLE_TAG')

        if tag != VERSION:
            info = 'Git tag: {0} does not match the version of this app: {1}'.format(
                tag, VERSION
            )
            sys.exit(info)


setup(
    version=VERSION,
    cmdclass={
        'verify': VerifyVersionCommand,
    }
)
