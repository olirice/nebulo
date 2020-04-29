# pylint: disable=invalid-name

from nebulo.gql.alias import Int, ScalarType, String
from sqlalchemy import types
from sqlalchemy.dialects import postgresql

DateTimeType = ScalarType(name="DateTime", serialize=str)
DateType = ScalarType(name="Date", serialize=str)
TimeType = ScalarType(name="Time", serialize=str)
UUIDType = ScalarType(name="UUID", serialize=str)
INETType = ScalarType(name="INET", serialize=str)
CIDRType = ScalarType(name="CIDR", serialize=str)

Typemap = {
    # Number
    types.Integer: Int,
    types.INTEGER: Int,
    types.String: String,
    # Text
    types.Text: String,
    types.Unicode: String,
    types.UnicodeText: String,
    # Date
    types.Date: DateType,
    types.Time: TimeType,
    types.DateTime: DateTimeType,
    postgresql.TIMESTAMP: DateTimeType,
    # Other
    postgresql.UUID: String,
    postgresql.INET: String,
    postgresql.CIDR: String,
}
