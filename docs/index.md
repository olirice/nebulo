# Nebulous

<p>
    <a href="https://github.com/olirice/nebulous/actions">
        <img src="https://github.com/olirice/nebulous/workflows/Tests/badge.svg" alt="Test Status">
    </a>
    <a href="https://github.com/olirice/nebulous/actions">
        <img src="https://github.com/olirice/nebulous/workflows/pre-commit%20hooks/badge.svg" alt="Pre-commit Status">
    </a>
</p>

**Documentation**: [https://olirice.github.io/nebulous/](https://olirice.github.io/nebulous/)

**Instant GraphQL API for PostgreSQL**


Nebulous [reflects](https://en.wikipedia.org/wiki/Reflection_(computer_programming)) a highly performant [GraphQL](https://graphql.org/learn/) API from an existing [PostgreSQL](https://www.postgresql.org/) database.



**WARNING: pre-alpha software**

## TL;DR

First, install nebulous
```shell
$ pip install nebulous
```

Then point the nebulous CLI at an existing  PostgreSQL database using connection string format `postgresql://<user>:<password>@<host>:<port>/<database_name>`
```shell
neb run -c postgresql://nebulous_user:password@localhost:4443/nebulous_db
```


Visit your shiny new GraphQL API at [http://localhost:5018/graphql](http://localhost:5018/graphql)



## Installation

**Requirements**: Python 3.7+, PostgreSQL 11+

Pip install the nebulous CLI

```shell
$ pip install nebulous
```

Next, check out the [quickstart](quickstart.md) guide for a small end-to-end example.

<p align="center">&mdash;&mdash;  &mdash;&mdash;</p>