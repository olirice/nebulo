from sqlalchemy import func, literal_column, select, text, type_coerce
from sqlalchemy.orm import column_property
from sqlalchemy.types import TEXT


class ComputedColumnsMixin:
    """ComputedColumnsMixin extends sqlalchemy.ext.automap_base to
    add sql functions as queryable columns on the sqlalchemy table object

    In order to be eligable to be a computed column, the sql function must
    take a row of the table type

    Example:

    create table user (
        id        serial primary key,
        user_name text not null
    );

    create function upper_user_name( rec user )
    returns varchar
    as $$ select upper(rec.user_name); $$
    language sql
    immutable;

    Will cause the SQLAlchemy Model for user to have a queryable
    column named user.upper_user_name
    """

    @classmethod
    def prepare(cls, engine=None, reflect=False, schema="public", *args, **kwargs):
        """Extend automap base to reflect computed columns"""
        super().prepare(engine, reflect, schema, *args, **kwargs)
        computed_col_list = engine.execute(
            text(
                """
            with parameter_count as (
                select
                    specific_name,
                    count(*) freq
                from
                    information_schema.parameters
                group by
                    specific_name
            )

            SELECT
                parameters.udt_name table_type_name,
                routines.routine_name computed_column_name
            FROM
                information_schema.routines
                inner join information_schema.parameters
                    ON routines.specific_name=parameters.specific_name
                inner join information_schema.tables
                    on parameters.udt_name = "tables".table_name
                    and routines.specific_schema = "tables".table_schema
                inner join parameter_count
                    on parameters.specific_name = parameter_count.specific_name
            WHERE
                parameters.data_type = 'USER-DEFINED'
                -- Only lookup cases when the tables row is the only parameter
                and parameter_count.freq = 1
               -- and routines.specific_schema=schema
            ORDER BY
                parameters.udt_name,
                routines.routine_name
        """
            ),
            {},  # {"schema": schema},
        ).fetchall()
        print(computed_col_list)

        # TODO(OR): update query to include return type for type_coerce below
        # TODO(OR): lookup available types by string returned from query above?

        for table in cls.__subclasses__():
            computed_cols = [v for k, v in computed_col_list if k == table.table_name]
            for col_name in computed_cols:
                col = column_property(
                    select(
                        [
                            type_coerce(
                                getattr(func, col_name)(literal_column(table.table_name)), TEXT
                            )
                        ]
                    )
                )
                # Set the name of the computed column.
                # Failing to set this name will cause it to default to something like
                # '%(34598286723 anon)s%' which graphene attempts to us in the sort argument enum
                setattr(col.columns[0], "name", col_name)

                # Assign the column to the model
                setattr(table, col_name, col)

                # register column as computed
                table.computed_columns.append(col_name)
