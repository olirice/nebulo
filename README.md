# Nebulo

<p>
    <a href="https://github.com/olirice/nebulo/actions">
        <img src="https://github.com/olirice/nebulo/workflows/Tests/badge.svg" alt="Test Status">
    </a>
    <a href="https://github.com/olirice/nebulo/actions">
        <img src="https://github.com/olirice/nebulo/workflows/pre-commit%20hooks/badge.svg" alt="Pre-commit Status">
    </a>
    <a href="https://badge.fury.io/py/nebulo"><img src="https://badge.fury.io/py/nebulo.svg" alt="PyPI version" height="18"></a>
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

![graphiql image](images/graphiql.png)

Next, check out the [docs](https://olirice.github.io/nebulo/introduction/) guide for a small end-to-end example.

<p align="center">&mdash;&mdash;  &mdash;&mdash;</p>
