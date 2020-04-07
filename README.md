# Nebulo

<p>
    <a href="https://github.com/olirice/nebulo/actions">
        <img src="https://github.com/olirice/nebulo/workflows/Tests/badge.svg" alt="Test Status" height="18">
    </a>
    <a href="https://github.com/olirice/nebulo/actions">
        <img src="https://github.com/olirice/nebulo/workflows/pre-commit%20hooks/badge.svg" alt="Pre-commit Status" height="18">
    </a>
    <a href="https://codecov.io/gh/olirice/nebulo"><img src="https://codecov.io/gh/olirice/nebulo/branch/master/graph/badge.svg" height="18"></a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Codestyle Black" height="18">
    </a>

</p>
<p>
    <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python version" height="18"></a>
    <a href="https://github.com/olirice/nebulo/blob/master/LICENSE"><img src="https://img.shields.io/pypi/l/markdown-subtemplate.svg" alt="License" height="18"></a>
    <a href="https://badge.fury.io/py/nebulo"><img src="https://badge.fury.io/py/nebulo.svg" alt="PyPI version" height="18"></a>
    <a href="https://pypi.org/project/nebulo/"><img src="https://img.shields.io/pypi/dm/nebulo.svg" alt="Download count" height="18"></a>
</p>

---

**Documentation**: <a href="https://olirice.github.io/nebulo" target="_blank">https://olirice.github.io/nebulo</a>

**Source Code**: <a href="https://github.com/olirice/nebulo" target="_blank">https://github.com/olirice/nebulo</a>

---

**Instant GraphQL API for PostgreSQL**

[Reflect](https://en.wikipedia.org/wiki/Reflection_(computer_programming)) a highly performant [GraphQL](https://graphql.org/learn/) API from an existing [PostgreSQL](https://www.postgresql.org/) database.

Nebulo is a python library for building GraphQL APIs on top of PostgreSQL. It has a command line interface for reflecting databases wtih 0 code, and can also be added to existing [SQLAlchemy](https://www.sqlalchemy.org/) projects.

In contrast to existing options in the python ecosystem, Nebulo optimizes underlying SQL queries to solve the [N+1 query problem](https://stackoverflow.com/questions/97197/what-is-the-n1-selects-problem-in-orm-object-relational-mapping) and minimize database IO. The result is a blazingly fast API with consistent performance for arbitrarily nested queries.

**WARNING: Pre-Alpha Software**

## TL;DR

First, install nebulo
```shell
$ pip install nebulo
```

Then point the nebulo CLI at an existing  PostgreSQL database using connection string format `postgresql://<user>:<password>@<host>:<port>/<database_name>`
```shell
neb run -c postgresql://nebulo_user:password@localhost:4443/nebulo_db
```


Visit your shiny new GraphQL API at [http://localhost:5018/graphql](http://localhost:5018/graphql)

![graphiql image](docs/images/graphiql.png)

Next, check out the [docs](https://olirice.github.io/nebulo/introduction/) guide for a small end-to-end example.

<p align="center">&mdash;&mdash;  &mdash;&mdash;</p>
