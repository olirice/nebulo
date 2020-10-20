## Authentication

The approach to authentication and row level security were shamelessly borrowed from the [postgraphile](https://www.graphile.org/) project, a similar (but much more mature) PostgreSQL to GraphQL project written in Javascript.

Please see [their security documentation](https://www.graphile.org/postgraphile/security/) for best practices when setting up secure auth for api user roles.

For a complete usage, see [the row level security example project](https://github.com/olirice/nebulo/tree/master/examples/row_level_security)


Note that JWT identifier and JWT secret can be passed to the nebulo CLI via `--jwt-identifier "public.my_jwt"` and `--jwt-secret "my_jwt_secret"` to cause functions returning the JWT type to reflect correctly.

If the JWT type contains a `role` field, that role will be used to execute SQL statements for authenticated user's requests. Anonymous users' requests execute with the connections default role unless a default role is passed using the `--default-role` option

