from setuptools import setup, find_packages

setup(
    name="csql",
    version="0.0.1",
    description="CSQL Continuous SQL",
    author="Oliver Rice",
    author_email="oliver@oliverrice.com",
    license="TBD",
    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    packages=find_packages('src/main/python'),
    package_dir={'': 'src/main/python'},
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'csql=csql.cli.csql_cli:main',
        ],
    },
    test_suite='nose.collector',
    tests_require=['nose==1.3.7'],
    install_requires=[
        'moz_sql_parser==2.44.19084'
    ]
)
