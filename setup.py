import re
import os.path
import sys

from setuptools import setup, find_packages
from mypyc.build import mypycify

package_name = "py3rijndael"
py_version = sys.version_info[:2]

# reading package's version
with open(
    os.path.join(os.path.dirname(__file__), package_name, "__init__.py")
) as v_file:
    re_groups = re.search(r'__version__ = "(.*)"', v_file.read())
    if re_groups:
        package_version = re_groups.group(1)
    else:
        raise Exception("Can't find version in __init__.py")

setup(
    name=package_name,
    version=package_version,
    author="Mahdi Ghanea.g",
    description="Rijndael algorithm library for Python3.",
    long_description=open("README.rst").read(),
    url="https://github.com/meyt/py3rijndael",
    packages=find_packages(),
    license="MIT License",
    ext_modules=mypycify(
        [
            "--strict",
            "py3rijndael/__init__.py",
            "py3rijndael/constants.py",
            "py3rijndael/paddings.py",
            "py3rijndael/rijndael.py",
        ]
    ),
    setup_requires=["mypy"],
    classifiers=[
        "Environment :: Console",
        "Topic :: Security :: Cryptography",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
