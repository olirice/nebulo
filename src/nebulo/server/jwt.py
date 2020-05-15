from typing import Any, Awaitable, Callable, Dict, Optional

import jwt
from starlette.exceptions import HTTPException
from starlette.requests import Request


def get_jwt_claims_handler(secret: Optional[str]) -> Callable[[Request], Awaitable[Dict[str, Any]]]:
    """Return a function that retrieves and decodes JWT claims from the Starlette Request"""

    async def get_jwt_claims(request: Request) -> Dict[str, Any]:
        """Retrieve the JWT claims from the Starlette Request"""

        return {}

        if secret is None:
            return {}

        if "Authorization" not in request.headers:
            return {}

        auth = request.headers["Authorization"]
        try:
            scheme, token = auth.split()
            if scheme.lower() == "bearer":
                contents = jwt.decode(token, secret, algorithms=["HS256"])
                return contents
        except jwt.exceptions.DecodeError:
            raise HTTPException(401, "Invalid JWT credentials")
        except jwt.exceptions.ExpiredSignatureError:
            raise HTTPException(401, "JWT has expired. Please reauthenticate")
        # Generically catch all PyJWT errors
        except jwt.exceptions.PyJWTError as exc:
            raise HTTPException(401, str(exc))
        return {}

    return get_jwt_claims
