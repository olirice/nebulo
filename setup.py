import os

from setuptools import find_packages, setup


def read_package_variable(key, filename="__init__.py"):
    """Read the value of a variable from the package without importing."""
    module_path = os.path.join("src/nebulo", filename)
    with open(module_path) as module:
        for line in module:
            parts = line.strip().split(" ", 2)
            if parts[:-1] == [key, "="]:
                return parts[-1].strip("'").strip('"')
    return None


setup(
    name="nebulo",
    version=read_package_variable("VERSION"),
    description="Nebulo: GraphQL API for PostgreSQL",
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
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    entry_points={
        "console_scripts": ["nebulo=nebulo.cli:main", "neb=nebulo.cli:main"],
        "pygments.lexers": ["graphqllexer=nebulo.lexer:GraphQLLexer"],
    },
    install_requires=[
        "aiofiles==0.5.*",
        "appdirs==1.4.3",
        "asyncpg",
        "cachetools==4.0.*",
        "click==7.*",
        'dataclasses; python_version<"3.7"',
        "flupy==1.*",
        "graphql-core==3.1.*",
        "inflect==4.1.*",
        "parse==1.15.*",
        "psycopg2-binary>=2.8.*",
        "pyjwt==1.7.*",
        "starlette==0.14.*",
        "sqlalchemy>=1.4.0",
        "typing-extensions",
        "uvicorn==0.13.*",
    ],
    extras_require={
        "test": ["pytest", "pytest-cov", "requests", "pytest-asyncio"],
        "dev": ["pylint", "black", "sqlalchemy-stubs", "pre-commit"],
        "nvim": ["neovim", "python-language-server"],
        "docs": ["mkdocs", "pygments", "pymdown-extensions", "mkautodoc"],
    },
)
