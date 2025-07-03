from pydantic import BaseModel


class UserInfo(BaseModel):
    dirname: str
    display_name: str
    given_name: str
    surname: str
    email: str
