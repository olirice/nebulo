# Supported Entities

There is automatic reflection support for:

- Tables
- Views
- Functions



### Views

To reflect correctly, views must

```
COMMENT ON TABLE [schema].[table]
IS E'@primary_key (part_1, part_2)';
```

Views also support a virtual foreign key comment to establish a connection to the broader graph.

```
@foreign_key (variant_id, key2) references public.variant (id, key2)
```
OR
```
@foreign_key (variant_id, key2) references public.variant (id, key2) LocalNameForRemote RemoteNameForLocal'
```
