# Comment Directives (Experimental)

Some SQL comments are interpreted as directives and impact how nebulo reflects database entities.

## Exclude

*Usage*

`@exclude ...`


*Description*

The exclude directive can be applied to tables, views, foreign keys, table columns, or view columns. The mutation or query you'd like the entity to be omitted from may be described with a combination of the following.

**Table/View Allowed Params:**

- create
- read
- read_one
- read_all
- update
- delete

**Column Allowed Params:**

- create
- read
- update
- delete

**Foreign Key Allowed Params:**
- read


For example, the directive `@exclude delete, update` would make the entity immutable.

Note:
- that `read` is equivalent to `read_one` and `read_all` together.
- `@exclude connection` prevents any associations to the table via foreign keys

#### Example

The following examples show how you could exclude a column named `password_hash` from being exposed through the GraphQL API using SQL or SQLAlchemy.


**SQL**
```sql
create table account (
	username text not null primary key,
	password_hash text not null,
);

comment on column account.password_hash is E'@exclude create, read, update, delete';
```


**SQLAlchemy**
```python
class Account(Base):
    __tablename__ = "account"

    username = Column(Text, primary_key=False)
    password_hash = Column(Text, comment="@exclude create, read, update, delete")
```

## Name

*Usage*

   `@name <name>`


*Description*


The name directive can be applied to tables, and table columns to override the GraphQL type's associated with the commented entity.

For example, the directive `@name ShippingAddress` on an `address` table would result in the GraphQL type being named `ShippingAddress`.
