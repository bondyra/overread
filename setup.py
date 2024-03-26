"""Python setup.py for overread package"""

import io
import os
from setuptools import find_packages, setup


__version__ = "0.2.1"


def read(*paths, **kwargs):
    """Read the contents of a text file safely
    >>> read("README.md")
    ...
    """

    content = ""
    with io.open(
        os.path.join(os.path.dirname(__file__), *paths),
        encoding=kwargs.get("encoding", "utf8"),
    ) as open_file:
        content = open_file.read().strip()
    return content


def read_requirements(path):
    return [line.strip() for line in read(path).split("\n") if not line.startswith(('"', "#", "-", "git+"))]


setup(
    name="overread",
    version=__version__,
    description="overread",
    url="https://github.com/bondyra/overread/",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="bondyra",
    packages=find_packages(exclude=["tests", ".github"]),
    package_data={
        'overread': ['builtin_modules/*'],
    },
    entry_points={"console_scripts": ["ov = overread.__main__:main"]},
    extras_require={"test": read_requirements("requirements-test.txt")},
)
