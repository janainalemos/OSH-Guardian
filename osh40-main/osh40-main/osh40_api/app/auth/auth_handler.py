### Based in this example: https://testdriven.io/blog/fastapi-jwt-auth/


import time
import jwt
from typing import Dict
from osh40_api.app.auth.model import User
from decouple import config


JWT_SECRET = config("OSH40_KEY_JWT")
JWT_ALGORITHM = config("JWT_ALGORITHM")


def token_response(token: str):
    return {
        "access_token": token
    }


def signJWT(user: User) -> Dict[str, str]:
    payload = {
        "university": user.university,
        "owner": user.owner,
        "email": user.email,
        "service": user.service,
        "expires": time.time() + 600
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return token_response(token)


def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}
