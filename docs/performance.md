# Performance

*Page Not Complete*

Key Points:
- All queries are handled in a single round-trip to the database. No [N+1 problems](https://stackoverflow.com/questions/97197/what-is-the-n1-selects-problem-in-orm-object-relational-mapping) here!
- SQL queries only fetch requested fields which also (reduces IO and improves performance)
- SQL queries return JSON which significantly reduces database IO when joins are present
