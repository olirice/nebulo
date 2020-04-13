from setuptools import find_packages, setup

setup(
    name="nebulo",
    version="0.0.3",
    description="Nebulo: Reflect RDBMS to GraphQL API",
    author="Oliver Rice",
    author_email="oliver@oliverrice.com",
    license="MIT",
    url="https://github.com/olirice/nebulo",
    project_urls={
        "Documentation": "https://olirice.github.io/nebulo/",
        "Source Code": "https://github.com/olirice/nebulo",
    },
    keywords="graphql sqlalchemy sql api python",
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.7",
    packages=find_packages("src/main/python"),
    package_dir={"": "src/main/python"},
    include_package_data=True,
    entry_points={
        "console_scripts": ["nebulo=nebulo.cli:main", "neb=nebulo.cli:main"],
        "pygments.lexers": ["graphqllexer=nebulo.lexer:GraphQLLexer"],
    },
    install_requires=[
        "sqlalchemy==1.3.15",
        "psycopg2-binary==2.8.4",
        "graphql-core==3.1.0",
        "flask==1.1.1",
        "click==7.1.1",
        "inflect==4.1.0",
        "cachetools==4.0.0",
        "starlette==0.13.2",
        "databases[postgresql]==0.2.6",
        "uvicorn==0.11.3",
    ],
    extras_require={
        "test": ["pytest", "pytest-cov"],
        "dev": ["pylint", "black", "sqlalchemy-stubs", "pre-commit"],
        "nvim": ["neovim", "python-language-server"],
        "docs": ["mkdocs", "pygments", "pymdown-extensions"],
    },
)
