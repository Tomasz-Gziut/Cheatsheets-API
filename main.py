from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.users import router as users_router
from routers.notes import router as notes_router
from routers.login import router as login_router
from config import ALLOWED_ORIGINS

app = FastAPI(title="Cheatsheets API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.api_route("/", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}


app.include_router(login_router)
app.include_router(users_router)
app.include_router(notes_router)
