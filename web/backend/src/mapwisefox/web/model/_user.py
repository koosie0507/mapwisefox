from pydantic import BaseModel


class UserInfo(BaseModel):
    dirname: str
    issuer: str
    subject: str
    display_name: str
    email: str
