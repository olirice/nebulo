# Nebulo Example:


# Start the database
```shell
docker run --rm --name nebulo_rls -p 5523:5432 -d -e POSTGRES_DB=nebulo_example -e POSTGRES_PASSWORD=app_password POSTGRES_USER=app_user -d postgres
```

```shell
docker cp ./setup.sql nebulo_rls:/docker-entrypoint-initdb.d/setup.sql
```

```shell
docker exec -u postgres nebulo_rls psql nebulo_example app_user -f docker-entrypoint-initdb.d/setup.sql
```

Then start the webserver
```shell
neb run -c postgresql://nebulo_user:password@localhost:4443/nebulo_db --default-role anon_api_user --jwt-identifier public.jwt --jwt-secret super_duper_secret --reload
```
