#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name="p2p-tribune",
    version="1.5.0",

    packages=find_packages(),
    install_requires=["python-dateutil",
                      "requests>=2.0",
                      "iso8601",
                      "pytz",
                    ],
    entry_points={
        'console_scripts': [
            'p2pci = p2p.command:content_item_cli',
        ],
    },
    test_suite='p2p.tests',

    # project info
    author="Ryan Mark, Tribune News Applications",
    author_email="newsapps@tribune.com",
    description="Tribune Content Services API wrapper",
    long_description="Python wrapper for the Tribune Corp. Content Services API. "
                "The CMS is also known as \"Power to the Producers,\" hence "
                "the \"p2p\" name you'll see everywhere.",
    url="http://github.com/newsapps/p2p-python",
    license="MIT",
    keywords=['Development Status :: 4 - Beta',
              'License :: OSI Approved :: MIT License',
              'Operating System :: OS Independent',
              'Programming Language :: Python',
              'Topic :: Internet',
              ],
)
