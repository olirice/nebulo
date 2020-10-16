import typing

from sqlalchemy import Text, func, literal, select
from sqlalchemy.sql.selectable import Select


def build_claims(jwt_claims: typing.Dict[str, typing.Any], default_role: typing.Optional[str]) -> Select:
    """Emit statement to set 'jwt.claims.<key>' for each claim in claims dict
    and a 'role'
    """
    # Setting local variables an not be done in prepared statement
    # since JWT claims are signed, literal binds should be ok
    role_key = "role"

    # Set all jwt.claims.*
    claims = [
        func.set_config(
            literal("jwt.claims.").op("||")(func.cast(claim_key, Text())),
            func.cast(str(claim_value), Text()),
            True,
        )
        for claim_key, claim_value in jwt_claims.items()
    ]
    # Set all role claim if exists from jwt
    if role_key in jwt_claims:
        claims.append(
            func.set_config(
                func.cast(role_key, Text()),
                func.cast(str(jwt_claims[role_key]), Text()),
                True,
            )
        )
    # Set default role from config if provided
    elif default_role is not None:
        claims.append(
            func.set_config(
                func.cast(role_key, Text()),
                func.cast(str(default_role), Text()),
                True,
            )
        )
    return select(claims)
