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

Nebulo [reflects](https://en.wikipedia.org/wiki/Reflection_(computer_programming)) a highly performant [GraphQL](https://graphql.org/learn/) API from an existing [PostgreSQL](https://www.postgresql.org/) database.



**WARNING: pre-alpha software**

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



## Installation

**Requirements**: Python 3.7+, PostgreSQL 11+

Pip install the nebulo CLI

```shell
$ pip install nebulo
```

Next, check out the [quickstart](https://olirice.github.io/nebulo/quickstart/) guide for a small end-to-end example.

<p align="center">&mdash;&mdash;  &mdash;&mdash;</p>
