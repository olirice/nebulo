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
        "sqlalchemy==1.3.11",
        "psycopg2-binary==2.8.4",
        "graphql-core==2.2.1",
        "flask==1.1.1",
        "flask-graphql==2.0.0",
        "click==7.0",
        "inflect==3.0.2",
    ],
    extras_require={
        "test": ["pytest", "pytest-cov"],
        "dev": ['pylint', 'black', 'sqlalchemy-stubs'],
        "nvim": ['neovim', 'python-language-server']
        },
)
