## Authentication

The approach to authentication and row level security were shamelessly borrowed from the [postgraphile](https://www.graphile.org/) project, a similar (but much more mature) PostgreSQL to GraphQL project written in javascript.


Please see [their security documentation](https://www.graphile.org/postgraphile/security/) for instructions on setting up secure auth for api users.


Note that JWT identifier and JWT secret can be passed to the nebulo CLI via `--jwt-identifier "public.my_jwt"` and `--jwt-secret "my_jwt_secret"` to cause functions returning the JWT type to reflect correctly.

