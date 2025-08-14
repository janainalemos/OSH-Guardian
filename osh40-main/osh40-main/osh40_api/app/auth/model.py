### Based in this example: https://testdriven.io/blog/fastapi-jwt-auth/

from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    university: str = Field(...)
    owner: str = Field(...)
    email: EmailStr = Field(...)
    service: str = Field(...)
