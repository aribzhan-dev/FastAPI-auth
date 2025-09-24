from pydantic import EmailStr, BaseModel
from typing import Annotated
from annotated_types import MinLen, MaxLen



class CreateUser(BaseModel):
    # username : str = field(..., min_length=3, man_length=30) bu eski versiyasi
    username: Annotated[str, MinLen(3), MaxLen(30)]
    email: EmailStr