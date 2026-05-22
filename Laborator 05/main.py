import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

load_dotenv()

DATABASE_PATH = os.environ.get("DATABASE_PATH", "sarcini.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-laborator-05")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
TOKEN_MINUTES = int(os.environ.get("EXPIRARE_TOKEN_MINUTE", "30"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="autentificare")


def setup_database() -> None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS utilizatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            parola_hash TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS sarcini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titlu TEXT NOT NULL,
            descriere TEXT,
            finalizata INTEGER DEFAULT 0,
            utilizator_id INTEGER NOT NULL,
            data_crearii TEXT NOT NULL,
            FOREIGN KEY (utilizator_id) REFERENCES utilizatori(id)
        )
        """
    )
    connection.commit()
    connection.close()


def get_database():
    connection = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
    finally:
        connection.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_database()
    yield


app = FastAPI(title="Homemade To Do", version="1.0.0", lifespan=lifespan)


class UserCreate(BaseModel):
    email: str = Field(min_length=5, max_length=100)
    parola: str = Field(min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if "@" not in normalized or "." not in normalized.split("@")[-1]:
            raise ValueError("Adresa de email nu este valida.")
        return normalized


class TaskCreate(BaseModel):
    titlu: str = Field(min_length=1, max_length=200)
    descriere: str | None = Field(default=None, max_length=1000)


class TaskUpdate(BaseModel):
    titlu: str | None = Field(default=None, min_length=1, max_length=200)
    descriere: str | None = Field(default=None, max_length=1000)
    finalizata: bool | None = None


def to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def password_matches(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_token(payload: dict) -> str:
    token_data = payload.copy()
    token_data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_MINUTES)
    return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    database: sqlite3.Connection = Depends(get_database),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalid.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirat.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalid.")

    user = database.execute(
        "SELECT * FROM utilizatori WHERE email = ?",
        (email,),
    ).fetchone()
    if user is None:
        raise HTTPException(status_code=401, detail="Utilizatorul nu exista.")
    return user


def find_task_or_404(
    database: sqlite3.Connection,
    task_id: int,
    user_id: int,
) -> sqlite3.Row:
    task = database.execute(
        "SELECT * FROM sarcini WHERE id = ? AND utilizator_id = ?",
        (task_id, user_id),
    ).fetchone()
    if task is None:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost gasita.")
    return task


@app.get("/healthz")
def health_check():
    return {"status": "ok"}


@app.post("/inregistrare", status_code=201)
def register_user(
    user: UserCreate,
    database: sqlite3.Connection = Depends(get_database),
):
    existing_user = database.execute(
        "SELECT id FROM utilizatori WHERE email = ?",
        (user.email,),
    ).fetchone()
    if existing_user:
        raise HTTPException(status_code=400, detail="Emailul este deja inregistrat.")

    database.execute(
        "INSERT INTO utilizatori (email, parola_hash) VALUES (?, ?)",
        (user.email, hash_password(user.parola)),
    )
    database.commit()
    return {"mesaj": "Cont creat cu succes.", "email": user.email}


@app.post("/autentificare")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    database: sqlite3.Connection = Depends(get_database),
):
    email = form.username.strip().lower()
    user = database.execute(
        "SELECT * FROM utilizatori WHERE email = ?",
        (email,),
    ).fetchone()

    if user is None or not password_matches(form.password, user["parola_hash"]):
        raise HTTPException(status_code=401, detail="Email sau parola incorecta.")

    token = create_token({"sub": user["email"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/utilizatori/eu")
def read_my_user(current_user=Depends(get_current_user)):
    return {"id": current_user["id"], "email": current_user["email"]}


@app.get("/sarcini")
def list_tasks(
    doar_nefinalizate: bool = False,
    database: sqlite3.Connection = Depends(get_database),
    current_user=Depends(get_current_user),
):
    if doar_nefinalizate:
        rows = database.execute(
            """
            SELECT * FROM sarcini
            WHERE utilizator_id = ? AND finalizata = 0
            ORDER BY id
            """,
            (current_user["id"],),
        ).fetchall()
    else:
        rows = database.execute(
            "SELECT * FROM sarcini WHERE utilizator_id = ? ORDER BY id",
            (current_user["id"],),
        ).fetchall()

    return [to_dict(row) for row in rows]


@app.post("/sarcini", status_code=201)
def create_task(
    task: TaskCreate,
    database: sqlite3.Connection = Depends(get_database),
    current_user=Depends(get_current_user),
):
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = database.execute(
        """
        INSERT INTO sarcini (titlu, descriere, utilizator_id, data_crearii)
        VALUES (?, ?, ?, ?)
        """,
        (task.titlu, task.descriere, current_user["id"], created_at),
    )
    database.commit()

    new_task = database.execute(
        "SELECT * FROM sarcini WHERE id = ?",
        (cursor.lastrowid,),
    ).fetchone()
    return to_dict(new_task)


@app.get("/sarcini/{task_id}")
def read_task(
    task_id: int,
    database: sqlite3.Connection = Depends(get_database),
    current_user=Depends(get_current_user),
):
    task = find_task_or_404(database, task_id, current_user["id"])
    return to_dict(task)


@app.put("/sarcini/{task_id}")
def update_task(
    task_id: int,
    changes: TaskUpdate,
    database: sqlite3.Connection = Depends(get_database),
    current_user=Depends(get_current_user),
):
    task = to_dict(find_task_or_404(database, task_id, current_user["id"]))

    title = changes.titlu if changes.titlu is not None else task["titlu"]
    description = (
        changes.descriere if changes.descriere is not None else task["descriere"]
    )
    done = int(changes.finalizata) if changes.finalizata is not None else task["finalizata"]

    database.execute(
        """
        UPDATE sarcini
        SET titlu = ?, descriere = ?, finalizata = ?
        WHERE id = ? AND utilizator_id = ?
        """,
        (title, description, done, task_id, current_user["id"]),
    )
    database.commit()

    updated_task = find_task_or_404(database, task_id, current_user["id"])
    return to_dict(updated_task)


@app.patch("/sarcini/{task_id}/finalizeaza")
def complete_task(
    task_id: int,
    database: sqlite3.Connection = Depends(get_database),
    current_user=Depends(get_current_user),
):
    find_task_or_404(database, task_id, current_user["id"])
    database.execute(
        "UPDATE sarcini SET finalizata = 1 WHERE id = ? AND utilizator_id = ?",
        (task_id, current_user["id"]),
    )
    database.commit()

    completed_task = find_task_or_404(database, task_id, current_user["id"])
    return to_dict(completed_task)


@app.delete("/sarcini/{task_id}")
def delete_task(
    task_id: int,
    database: sqlite3.Connection = Depends(get_database),
    current_user=Depends(get_current_user),
):
    find_task_or_404(database, task_id, current_user["id"])
    database.execute(
        "DELETE FROM sarcini WHERE id = ? AND utilizator_id = ?",
        (task_id, current_user["id"]),
    )
    database.commit()
    return {"mesaj": f"Sarcina cu ID-ul {task_id} a fost stearsa."}


app.mount("/", StaticFiles(directory="static", html=True), name="static")
