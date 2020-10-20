# Nebulo Row Level Security Example:

This example leverages PostgreSQL [roles](https://www.postgresql.org/docs/8.1/user-manag.html) and [row level security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html) with nebulo's builtin [JWT](https://jwt.io/) support to expose a GraphQL API with different permissions for anonymous and authenticated users.

Permissions are scoped such that:

- Anonymous users may:
    - Create an account
    - See blog posts

- Authenticated users may:
    - Edit their own account info
    - Create a blog post
    - Edit their own blog posts
    - See blog posts

# Start the database
```shell
docker run --rm --name nebulo_rls -p 5523:5432 -d -e POSTGRES_DB=nebulo_example -e POSTGRES_PASSWORD=app_password -e POSTGRES_USER=app_user -d postgres
```

```shell
docker cp ./setup.sql nebulo_rls:/docker-entrypoint-initdb.d/setup.sql
```

```shell
docker exec -u postgres nebulo_rls psql nebulo_example app_user -f docker-entrypoint-initdb.d/setup.sql
```

Then start the webserver
```shell
neb run -c postgresql://nebulo_user:password@localhost:4443/nebulo_db --default-role anon_api_user --jwt-identifier public.jwt --jwt-secret super_duper_secret
```


Explore the GraphQL API at [http://0.0.0.0:5034/graphiql](http://0.0.0.0:5034/graphiql)
