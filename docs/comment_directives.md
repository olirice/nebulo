# Comment Directives

Some SQL comments are interpreted as directives and impact how nebulo reflects database entities.

## Exclude


`@exclude ...`


The exclude directive can be applied to tables, views, functions, table columns, or view columns. The mutation or query you'd like the entity to be omitted from may be described with a combination of the following verbs.

**Allowed Verbs:**

- insert
- update
- delete
- read

For example, the directive `@exclude delete, update` would make the entity immutable.


#### Example

The following examples show how you could exclude a column named `password_hash` from being exposed through the GraphQL API using SQL or SQLAlchemy.


**SQL**
```sql
create table account (
	username text not null primary key,
	password_hash text not null,
);

comment on column account.password_hash is E'@exclude insert, update, delete, read';
```


**SQLAlchemy**
```python
class Account(Base):
    __tablename__ = "account"

    username = Column(Text, primary_key=False)
    password_hash = Column(Text, comment="@exclude insert, update, delete, read")
```
