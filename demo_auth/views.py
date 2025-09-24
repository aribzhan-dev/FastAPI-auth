# import secrets
# import uuid
# from time import time
# from fastapi import APIRouter, Depends, HTTPException, status, Header, Response, Cookie
# from fastapi.security import HTTPBasicCredentials, HTTPBasic
# from typing import Annotated, Any
#
# router = APIRouter(prefix="/auth", tags=["Auth"])
#
# security = HTTPBasic()
#
# @router.get("/basic-auth/")
# def basic_auth_credentials(
#     credentials: Annotated[HTTPBasicCredentials, Depends(security)],
# ):
#     return {
#         "message": "Success",
#         "user": credentials.username,
#         "password": credentials.password,
#     }
# usernames_to_password = {
#     "admin": "qwertyy",
#     "qwertyy": "admin",
# }
#
# static_auth_token_to_username = {
#     "dc5002db78443636d63f243bc538b615": "john",
#     "f2040a2ed18f15e7823e2a91c27b2ee8": "admin"
# }
#
#
#
#
#
# def get_auth_user_username(
#         credentials: Annotated[HTTPBasicCredentials, Depends(security)]
# ):
#     unauthed_ex = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Invalid username or password",
#         headers={"WWW-Authenticate": "Basic"},
#     )
#     correct_password = usernames_to_password.get(credentials.username)
#     if correct_password is None:
#         raise unauthed_ex
#
#
#     #secrets
#     if not secrets.compare_digest(
#         credentials.password.encode("utf-8"),
#         correct_password.encode("utf-8"),
#     ):
#         raise unauthed_ex
#
#     return credentials.username
#
#
#
# def get_username_by_static_auth_token(
#         static_token: str = Header(alias="x-auth-token")
# ) -> str:
#     if username:= static_auth_token_to_username.get(static_token):
#         return username
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="token invalid",
#     )
#
#
#
#
# # auth by base auth
# @router.get("/basic-auth-username/")
# def basic_auth_username(
#     auth_username: str = Depends(get_auth_user_username)
# ):
#     return {
#         "message": f"Hi {auth_username}",
#         "username": auth_username,
#     }
#
#
#
# # auth by header
# @router.get("/some-http-header-auth/")
# def demo_auth_some_http_header(
#     username: str = Depends(get_username_by_static_auth_token)
# ):
#     return {
#         "message": f"Hi {username}",
#         "username": username,
#     }
#
#
#
#
# COOKIES: dict[str, dict[str, Any]] = {}
# COOKIE_SESSION_ID_KEY = "web-app-session-id"
#
# def generate_session_id() -> str:
#     return uuid.uuid4().hex
#
#
#
# def get_session_data(
#         session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
# ) -> dict:
#     if session_id not in COOKIES:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Not authenticated",
#         )
#     return COOKIES[session_id]
#
#
# # auth by cookie
# @router.post("/login-cookie/")
# def demo_auth_login_set_cookie(
#     response : Response,
#     # auth_username: str = Depends(get_auth_user_username)
#     username: str = Depends(get_username_by_static_auth_token),
# ):
#     session_id = generate_session_id()
#     COOKIES[session_id] = {
#         "username": username,
#         "login_at": int(time())
#     }
#     response.set_cookie(COOKIE_SESSION_ID_KEY, session_id)
#     return {"result": "ok"}
#
#
#
# @router.get("/check-cookie/")
# def demo_auth_check_cookie(
#     user_session_data: dict = Depends(get_session_data)
# ):
#     username = user_session_data["username"]
#     return {
#         "message": f"Hello {username}",
#         **user_session_data,
#
#     }
#
#
# @router.get("/logout-cookie/")
# def demo_auth_logout_cookie(
#         response: Response,
#         session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
#         user_session_data: dict = Depends(get_session_data),
# ):
#     COOKIES.pop(session_id)
#     response.delete_cookie(COOKIE_SESSION_ID_KEY)
#     username = user_session_data["username"]
#     return {
#         "message": f"Bye {username}",
#     }






import os
import uuid
from time import time
from typing import Optional, Any
# Parol hashing
from passlib.context import CryptContext
from fastapi import APIRouter, Depends, HTTPException, Response, Cookie, status
from pydantic import BaseModel, EmailStr, Field

# Redis (async)
from redis.asyncio import Redis


# ----------------- Redis & Auth settings -----------------
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "604800"))  # 7 days
COOKIE_SESSION_ID_KEY = "web-app-session-id"

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

_redis_client: Optional[Redis] = None
async def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis_client

def _session_key(sid: str) -> str:
    return f"session:{sid}"

def _user_key(email: str) -> str:
    return f"user:{email.lower()}"

def _new_sid() -> str:
    return uuid.uuid4().hex

# ----------------- Pydantic bodies -----------------
class RegisterIn(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1)
    password: str = Field(min_length=6)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

# ----------------- Router -----------------
router = APIRouter(prefix="/auth", tags=["Auth"])

# ----------------- User helpers (Redis) -----------------
async def get_user(redis: Redis, email: str) -> dict[str, Any] | None:
    data = await redis.hgetall(_user_key(email))
    return data or None

async def create_user(redis: Redis, email: str, username: str, password: str) -> None:
    # parolni xeshlaymiz
    pwd_hash = _pwd_ctx.hash(password)
    await redis.hset(
        _user_key(email),
        mapping={
            "email": email.lower(),
            "username": username,
            "password_hash": pwd_hash,
        },
    )

# ----------------- Session helpers (Redis) -----------------
async def create_session(redis: Redis, email: str, username: str) -> str:
    sid = _new_sid()
    key = _session_key(sid)
    await redis.hset(key, mapping={
        "email": email.lower(),
        "username": username,
        "login_at": str(int(time())),
    })
    await redis.expire(key, SESSION_TTL_SECONDS)
    return sid

async def read_session(redis: Redis, sid: str) -> dict[str, Any] | None:
    if not sid:
        return None
    data = await redis.hgetall(_session_key(sid))
    return data or None

async def delete_session(redis: Redis, sid: str) -> None:
    await redis.delete(_session_key(sid))

# ----------------- Endpoints -----------------

@router.post("/register", status_code=201)
async def register(payload: RegisterIn, redis: Redis = Depends(get_redis)):
    """
    Foydalanuvchini Redis’da yaratadi: user:<email>
    {email, username, password_hash}
    """
    existing = await get_user(redis, payload.email)
    if existing:
        raise HTTPException(status_code=409, detail="User already exists")

    await create_user(redis, payload.email, payload.username, payload.password)
    return {"ok": True, "email": payload.email, "username": payload.username}

@router.post("/login-cookie/")
async def login_cookie(body: LoginIn, response: Response, redis: Redis = Depends(get_redis)):
    """
    JSON (email, password) qabul qiladi, Redis’dagi user bilan solishtiradi,
    sessiya yaratadi va cookie qo‘yadi.
    """
    user = await get_user(redis, body.email)
    if not user:
        # roʻyxatdan o‘tmagan bo‘lsa – xatolik
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please register first")

    pwd_hash = user.get("password_hash", "")
    if not pwd_hash or not _pwd_ctx.verify(body.password, pwd_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    sid = await create_session(redis, email=user["email"], username=user.get("username", ""))

    response.set_cookie(
        key=COOKIE_SESSION_ID_KEY,
        value=sid,
        httponly=True,
        samesite="Lax",
        secure=False,            # lokalda False; prod HTTPS’da True
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )
    return {"ok": True, "email": user["email"], "username": user.get("username", "")}

@router.get("/check-cookie/")
async def check_cookie(
    web_session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
    redis: Redis = Depends(get_redis),
):
    """
    Cookie’dagi SID bo‘yicha Redis’dan sessiyani tekshiradi.
    """
    sess = await read_session(redis, web_session_id)
    if not sess:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"ok": True, "session": sess}

@router.get("/logout-cookie/")
async def logout_cookie(
    response: Response,
    web_session_id: str = Cookie(alias=COOKIE_SESSION_ID_KEY),
    redis: Redis = Depends(get_redis),
):
    """
    Sessiyani o‘chiradi va cookie’ni tozalaydi.
    """
    await delete_session(redis, web_session_id)
    response.delete_cookie(key=COOKIE_SESSION_ID_KEY, path="/")
    return {"ok": True}