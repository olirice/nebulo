from typing import List
from sqlalchemy.engine import Connection
from sqlalchemy.sql.sqltypes import TypeEngine


class SQLFunction:
    def __init__(
        self,
        func_name: str,
        arg_names: List[str],
        arg_types: List["SQLAType"],
        return_type: "SQLAType",
    ):
        self.func_name = func_name
        self.arg_names = arg_names
        self.arg_types = arg_types
        self.return_type = return_type


def get_function_names(connection, schema=None):
    return ["authenticate"]


def reflect_function(connection, function_name: str, schema: str = "*"):
    """Connection is an engine"""

    dialect = connection.dialect
    domains = dialect._load_domains(connection)
    enum_recs = dialect._load_enums(connection)
    enums = dict(
        ((rec["name"],), rec) if rec["visible"] else ((rec["schema"], rec["name"]), rec)
        for rec in enum_recs
    )

    # TODO(OR): Make sure sqlite and mysql have the same private function
    def reflect_type(type_name: str) -> TypeEngine:
        """Returns the correct SQLAlchemy type given the SQL type
        as a string"""
        return dialect._get_column_info(
            name=None,
            format_type=type_name,
            default=None,
            notnull=False,
            domains=domains,
            enums=enums,
            schema=schema,
            comment=None,
        )["type"]

    # User Defined Types
    query = f"""
	SELECT
		pg_proc.oid,
		pg_proc.proname sql_func_name,
		CASE
		WHEN pg_proc.proretset
		THEN 'setof ' || pg_catalog.format_type(pg_proc.prorettype, NULL)
		ELSE pg_catalog.format_type(pg_proc.prorettype, NULL)
		END return_type,
		pg_proc.proargnames param_names,
		-- Type name as text
		array(select typname from pg_type, unnest(pg_proc.proargtypes) bc(d) where oid = bc.d) param_types
	    
	FROM pg_catalog.pg_proc
	    JOIN pg_catalog.pg_namespace ON (pg_proc.pronamespace = pg_namespace.oid)
	    JOIN pg_catalog.pg_language ON (pg_proc.prolang = pg_language.oid)
	WHERE
	    pg_proc.prorettype <> 'pg_catalog.cstring'::pg_catalog.regtype
	    AND (pg_proc.proargtypes[0] IS NULL
		OR pg_proc.proargtypes[0] <> 'pg_catalog.cstring'::pg_catalog.regtype)
	    
	    AND pg_proc.proname ilike '{function_name}'
	    AND pg_namespace.nspname like '{"public"}'
		and lanname <> 'c'
	    AND pg_catalog.pg_function_is_visible(pg_proc.oid);
    """
    print(function_name, schema)

    oid, sql_func_name, return_type, param_names, param_types = connection.execute(
        query
    ).first()
    param_types = [reflect_type(x) for x in param_types]
    return_type = reflect_type(return_type)

    sql_function = SQLFunction(
        func_name=sql_func_name,
        arg_names=param_names,
        arg_types=param_types,
        return_type=return_type,
    )

    return sql_function


# TODO(OR): Do something with these
# User Defined Types
"""
    SELECT n.nspname AS schema,
        pg_catalog.format_type ( t.oid, NULL ) AS name,
        t.typname AS internal_name,
        CASE
            WHEN t.typrelid != 0
            THEN CAST ( 'tuple' AS pg_catalog.text )
            WHEN t.typlen < 0
            THEN CAST ( 'var' AS pg_catalog.text )
            ELSE CAST ( t.typlen AS pg_catalog.text )
        END AS size,
        --pg_catalog.array_to_string (
            ARRAY( SELECT e.enumlabel
                    FROM pg_catalog.pg_enum e
                    WHERE e.enumtypid = t.oid
                    ORDER BY e.oid --), E'\n'
            ) AS tuple_elements,
		array(select attname from pg_attribute where attrelid = (select typrelid from pg_type where typname = t.typname) order by attnum) attr_name_arr,
		array(select typ.typname type_name from pg_attribute at1 left join pg_type typ on at1.atttypid = typ.oid where at1.attrelid = (select typrelid from pg_type where typname = t.typname)) attr_type_arr,
		array(select attnotnull from pg_attribute where attrelid = (select typrelid from pg_type where typname = t.typname) order by attnum) attr_not_null_arr,
		array(select attrelid from pg_attribute where attrelid = (select typrelid from pg_type where typname = t.typname) order by attnum) attr_id_arr,
		pg_catalog.obj_description ( t.oid, 'pg_type' ) AS description
    FROM pg_catalog.pg_type t
    LEFT JOIN pg_catalog.pg_namespace n
        ON n.oid = t.typnamespace
    WHERE ( t.typrelid = 0
            OR ( SELECT c.relkind = 'c'
                    FROM pg_catalog.pg_class c
                    WHERE c.oid = t.typrelid
                )
        )
        AND NOT EXISTS
            ( SELECT 1
                FROM pg_catalog.pg_type el
                WHERE el.oid = t.typelem
                    AND el.typarray = t.oid
            )
        AND n.nspname <> 'pg_catalog'
        AND n.nspname <> 'information_schema'
        AND pg_catalog.pg_type_is_visible ( t.oid )
        and pg_catalog.format_type = '{function_name}'
    ORDER BY 1, 2;

"""
