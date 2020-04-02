## Quickstart

For this example we're going to create a simple blogging platform. We'll start by creating a minimal database schema. Then we'll use nebulo to reflect our GraphQL API. Finally, we'll query from that API.

### Database Setup

First, we need to define our database schema. We need a table for accounts, and another for blog posts. All blog posts must be associated with an author in the accounts table.

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
(1, 1, 'First Post!'),
(2, 1, 'Sanitize all the things!'),
(3, 2, 'To Bite or not to Bite');
```

### GraphQL Schema

Now we're ready to reflect our new database schema into a GraphQL schema. The GraphQL schema document describes our API's types, fields, and relationships between entities. If you're new to GraphQL check out their [documentation](https://graphql.org/learn/) for more information.

To inspect the GraphQL schema
```shell
neb dump-schema -c postgresql://nebulo_user:password@localhost:4443/nebulo_db
```
where the connection string provided by `-c` is in the format `postgresql://<user>:<password>@<host>:<port>/<database_name>`

Which outputs the schema below
```graphql
schema {
  query: Query
}

type Account implements NodeInterface {
  nodeId: NodeID!
  id: Int!
  blogPostsByAuthorId(first: Int, after: Cursor, condition: BlogPostCondition): BlogPostConnection
  name: String!
  createdAt: String!
}

input AccountCondition {
  id: Int
  name: String
  createdAt: String
}

type AccountConnection {
  edges: [AccountEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}

type AccountEdge {
  cursor: Cursor
  node: Account
}

type BlogPost implements NodeInterface {
  nodeId: NodeID!
  id: Int!
  accountByAuthorId: Account
  title: String!
  body: String
  authorId: Int
  createdAt: String!
}

input BlogPostCondition {
  id: Int
  title: String
  body: String
  authorId: Int
  createdAt: String
}

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

scalar NodeID

interface NodeInterface {
  nodeId: NodeID!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: Cursor!
  endCursor: Cursor!
}

type Query {
  account(nodeId: NodeID): Account
  blogPost(nodeId: NodeID): BlogPost
  allAccounts(first: Int, after: Cursor, condition: AccountCondition): AccountConnection
  allBlogPosts(first: Int, after: Cursor, condition: BlogPostCondition): BlogPostConnection
}
```

Notice that our API detected the foreign key relationship between `Account` and `BlogPost` and created `blogPostsByAuthorId` and `accountByAuthorId` on their base types respectively.


### Query the API

To start the API server, execute `neb run` passing in a connection to the database.

```shell
neb run -c postgresql://nebulo_user:password@localhost:4443/nebulo_db
```

In addition to handling GraphQL requests, nebulo also serves the [GraphiQL explorer](https://github.com/graphql/graphiql) locally at [http://localhost:5018/graphql](http://localhost:5018/graphql).


![graphiql image](images/graphiql.png)

Enter your query in GraphiQL and click the arrow icon to execute it.

You're all done!
