from fastapi import FastAPI, Body, Request
import uvicorn
from pydantic import EmailStr, BaseModel
from uvicorn import lifespan
from core.models import Base, db_helper
from items_views import router as items_router
from users.views import router as users_router
from demo_auth.views import router as demo_router
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager




@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_helper.engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield





app = FastAPI(lifespan=lifespan)
# app.include_router(items_router)
# app.include_router(users_router, tags=["Users"])
app.include_router(demo_router, tags=["Auth"])
app.mount("/static", StaticFiles(directory="static"), name="static")



class CreateUser(BaseModel):
    email: EmailStr



# @app.get("/")
# def hello_index():
#     return {"message": "Hello World"}


# @app.get("/hello/")
# def hello(name: str = "World"):
#     name = name.strip().title()
#     return {"message": f"Hello {name}"}






app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:63342", "http://127.0.0.1:63342"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
def root():
    return FileResponse("templates/index.html")



if __name__ == "__main__":
    uvicorn.run("main:app", reload=True, host="127.0.0.1", port=9080)

