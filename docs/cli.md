## Command Line Interface

The CLI provides a path for deploying GraphQL APIs without writting any python code.

```text
Usage: neb [OPTIONS] COMMAND [ARGS]...

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  dump-schema  Dump the GraphQL Schema to stdout or file
  run          Run the GraphQL Web Server
```


#### neb run

Starts the GraphQL web server and serves the interactive documentation at `http://<host>:<port>/graphiql`

```text
Usage: neb run [OPTIONS]

  Run the GraphQL Web Server

Options:
  -c, --connection TEXT   Database connection string
  -p, --port INTEGER      Web server port
  -h, --host TEXT         Host address
  -w, --workers INTEGER   Number of parallel workers
  -s, --schema TEXT       SQL schema name
  --jwt-identifier TEXT   JWT composite type identifier e.g. "public.jwt"
  --jwt-secret TEXT       Secret key for JWT encryption
  --reload / --no-reload  Reload if source files change
  --default-role TEXT     Default PostgreSQL role for anonymous users
  --help                  Show this message and exit.
```



#### neb dump-schema

Export the GraphQL schema

```text
Usage: neb dump-schema [OPTIONS]

  Dump the GraphQL Schema to stdout or file

Options:
  -c, --connection TEXT    Database connection string
  -s, --schema TEXT        SQL schema name
  -o, --out-file FILENAME  Output file path
  --help                   Show this message and exit.
```
