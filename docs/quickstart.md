## Quickstart

For this example we're going to create a simple blogging platform. We'll start by creating a minimal database schema. Then we'll use nebulo to reflect our GraphQL API. Finally, we'll query from that API.

### Installation

Requires: Python 3.7+

```shell
pip install nebulo
```

### Database Setup

If you don't have PostgreSQL installed locally, the following docker command creates an instance with the connection string used for the remainder of the quickstart guide.

```shell
docker run --rm --name nebulo_demo -p 4443:5432 -d -e POSTGRES_DB=nebulo_db -e POSTGRES_PASSWORD=password -e POSTGRES_USER=nebulo_user -d postgres
```

Next, we need to define our database schema. We need a table for accounts, and another for blog posts. All blog posts must be associated with an author in the accounts table. Additionally, we don't want to allow users to update or delete their blog post.

```sql
-- blog_schema.sql

CREATE TABLE public.account (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE public.blog_post (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT,
    author_id INT REFERENCES account(id),
    created_at TIMESTAMP NOT NULL DEFAULT now()
);

INSERT INTO account (id, name) VALUES
(1, 'Oliver'),
(2, 'Buddy');

INSERT INTO blog_post (id, author_id, title) VALUES
(1, 1, 'First Post'),
(2, 1, 'Sanitize all the things!'),
(3, 2, 'To Bite or not to Bite');


COMMENT ON TABLE blog_post IS E'@exclude update, delete';
```

Note the comment to exclude updates and deletes from blog posts. The same comment format can also be applied to exclude columns from reflection e.g. password hashes.

### GraphQL Schema

Now we're ready to reflect the database schema into a GraphQL schema. The GraphQL schema document describes our API's types, fields, and relationships between entities. If you're new to GraphQL check out their [documentation](https://graphql.org/learn/) for more information.

To inspect the GraphQL schema
```shell
neb dump-schema -c postgresql://nebulo_user:password@localhost:4443/nebulo_db
```
where the connection string provided by `-c` is in the format `postgresql://<user>:<password>@<host>:<port>/<database_name>`

Which outputs the schema below

```graphql
type Query {
  """Reads a single Account using its globally unique ID"""
  account(nodeId: ID!): Account

  """Reads and enables pagination through a set of Account"""
  allAccounts(first: Int, last: Int, before: Cursor, after: Cursor, condition: accountCondition): AccountConnection

  """Reads a single BlogPost using its globally unique ID"""
  blogPost(nodeId: ID!): BlogPost

  """Reads and enables pagination through a set of BlogPost"""
  allBlogPosts(first: Int, last: Int, before: Cursor, after: Cursor, condition: blogPostCondition): BlogPostConnection
}

type Mutation {
  """Creates a single Account."""
  createAccount(input: CreateAccountInput!): CreateAccountPayload

  """Updates a single Account using its globally unique id and a patch."""
  updateAccount(input: UpdateAccountInput!): UpdateAccountPayload

  """Delete a single Account using its globally unique id and a patch."""
  deleteAccount(input: DeleteAccountInput!): DeleteAccountPayload

  """Creates a single BlogPost."""
  createBlogPost(input: CreateBlogPostInput!): CreateBlogPostPayload
}

type Account implements NodeInterface {
  nodeId: ID!
  id: Int!
  name: String!
  createdAt: DateTime!

  """Reads and enables pagination through a set of BlogPost"""
  blogPostsByIdToAuthorId(first: Int, last: Int, before: Cursor, after: Cursor, condition: blogPostCondition): BlogPostConnection!
}

"""An object with a nodeId"""
interface NodeInterface {
  """The global id of the object."""
  nodeId: ID!
}

scalar DateTime

type BlogPostConnection {
  edges: [BlogPostEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type BlogPostEdge {
  cursor: Cursor
  node: BlogPost
}

scalar Cursor


<abridged output>
```

Notice that our API detected the foreign key relationship between `Account` and `BlogPost` and created `blogPostsByIdToAuthorId` and `accountByAuthorIdToId` on their base types respectively.


### Query the API

To start the API server, execute `neb run` passing in a connection to the database.

```shell
neb run -c postgresql://nebulo_user:password@localhost:4443/nebulo_db
```

In addition to handling GraphQL requests, nebulo also serves the [GraphiQL explorer](https://github.com/graphql/graphiql) locally at [http://localhost:5034/graphiql](http://localhost:5034/graphiql).


![graphiql image](images/graphiql.png)

Enter your query in GraphiQL and click the arrow icon to execute it.

You're all done!
