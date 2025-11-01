from fastapi import FastAPI
from routers.users import router as users_router
from routers.notes import router as notes_router
from routers.login import router as login_router

app = FastAPI(title="Cheatsheets API", version="1.0")

app.include_router(login_router)
app.include_router(users_router)
app.include_router(notes_router)
