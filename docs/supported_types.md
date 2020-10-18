# Supported Types

There is first class support for the following PG types:

- Boolean
- Integer
- BigInteger
- Float
- Numeric (casts to float)
- Text
- Timestamp (as ISO 8601 string)
- UUID
- Composite (excludes nested composites)
- Enum

Other, unknown types, default to a String representation.
