from setuptools import setup, find_packages

setup(
    name="nebulous",
    version="0.0.1",
    description="Nebulous: Reflect RDBMS to GraphQL API",
    author="Oliver Rice",
    author_email="oliver@oliverrice.com",
    license="TBD",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6",
    packages=find_packages("src/main/python"),
    package_dir={"": "src/main/python"},
    include_package_data=True,
    entry_points={
        "console_scripts": ["nebulous=nebulous.cli:main", "neb=nebulous.cli:main"]
    },
    install_requires=[
        "click==7.0",
        "graphql-core",
        "sqlalchemy",
        "flask",
        "flask-graphql",
        "sqlalchemy_utils",
        "psycopg2-binary",
        "sqlparse==0.3.0",
        "inflect",
    ],
    extras_require={"test": ["pre-commit", "pytest", "pytest-cov"]},
)
