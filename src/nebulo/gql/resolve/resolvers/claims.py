import typing

from sqlalchemy import Text, func, literal, select
from sqlalchemy.sql.selectable import Select


def build_claims(jwt_claims: typing.Dict[str, typing.Any], default_role: typing.Optional[str] = None) -> Select:
    """Emit statement to set 'jwt.claims.<key>' for each claim in claims dict
    and a 'role'
    """
    # Setting local variables an not be done in prepared statement
    # since JWT claims are signed, literal binds should be ok

    # Keys with special meaning that should not be prefixed with 'jwt.claims'
    role_key = "role"
    special_keys = {role_key, "statement_timeout"}

    # Set all jwt.claims.*
    claims = [
        func.set_config(
            literal("jwt.claims.").op("||")(func.cast(claim_key, Text())),
            func.cast(str(claim_value), Text()),
            True,
        )
        for claim_key, claim_value in jwt_claims.items()
        if claim_key not in special_keys
    ]

    # Set role to default if exists and not provided by jwt
    if role_key not in jwt_claims and default_role is not None:
        jwt_claims[role_key] = default_role

    # Set keys with special meaning to postgres
    for key in special_keys:
        if key in jwt_claims:
            claims.append(
                func.set_config(
                    func.cast(key, Text()),
                    func.cast(str(jwt_claims[key]), Text()),
                    True,
                )
            )

    return select(claims)
