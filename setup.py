#!/usr/bin/env python3

from setuptools import setup

setup(
    name="pyReactor",
    version="0.1",
    py_modules=["reactor", "reactorPhysics", "legoReactor", "guiTemplate"],
    install_requires=[
        "numpy>=1.20",
        "scipy>=1.6",
        "matplotlib>=3.3",
        "pyserial>=3.0",
        "wxPython>=4.1",
    ],
    package_data={"": ["*.txt"]},
    author="Hridoy Kabiraj",
    author_email="rudrokabiraj@gmail.com",
    python_requires=">=3.6",
    entry_points={
        "console_scripts": [
            "pyReactor = legoReactor:main",
        ],
    },
)

