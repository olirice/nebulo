# Nebulo Example:

app.py is a minimal example showing how to integrate nebulo with an existing SQLAlchemy project.


# Start the database
```shell
docker run --rm --name nebulo_example_local -p 5522:5432 -d -e POSTGRES_DB=nebulo_example -e POSTGRES_PASSWORD=app_password POSTGRES_USER=app_user -d postgres
```

Then start the webserver

```shell
python app.py
```

Explore the GraphQL API at [http://0.0.0.0:5034/graphiql](http://0.0.0.0:5034/graphiql)
