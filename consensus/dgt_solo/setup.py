# Copyright 2026 DGT Network, Inc.
# Licensed under the Apache License, Version 2.0.
from setuptools import setup, find_packages

setup(
    name="dgt-solo",
    version="0.1.0",
    description="dgt-solo — single-node block sequencer engine for the REALM witness ledger",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pyzmq>=25",
        "protobuf>=4.25.1,<6",
    ],
    entry_points={
        "console_scripts": [
            "dgt-solo = dgt_solo.main:main",
        ],
    },
)
