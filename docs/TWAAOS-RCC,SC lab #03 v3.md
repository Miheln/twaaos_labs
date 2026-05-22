# Laborator #03: Persistență cu SQLite, CRUD și autentificare JWT

## Obiective

La finalul acestui laborator, studentul va fi capabil să:

- explice diferența dintre stocarea datelor în memorie și persistența pe disc;
- creeze și manipuleze o bază de date SQLite dintr-o aplicație FastAPI;
- implementeze un sistem CRUD complet (Create, Read, Update, Delete) cu persistență;
- descrie mecanismul JWT și rolul său în autentificarea serviciilor REST;
- protejeze endpoint-urile unui serviciu web folosind token-uri JWT;
- aplice validări avansate ale datelor de intrare cu Pydantic.

---

## 1. Persistența datelor

### 1.1 Problema datelor volatile

În laboratorul precedent, datele (lista de produse) erau stocate într-o variabilă Python (`inventar: list[Produs] = []`). Această abordare are o limitare fundamentală: **datele dispar la fiecare repornire a serverului**. Aceasta se numește stocare **volatilă** (*in-memory*).

Pentru o aplicație reală avem nevoie de **persistență** - datele trebuie să supraviețuiască repornirilor, căderilor de curent și altor evenimente neprevăzute.

### 1.2 SQLite - baza de date fără server (*serverless*)

**SQLite** este un motor de baze de date relaționale care stochează întreaga bază de date într-un singur fișier pe disc. Spre deosebire de MySQL sau PostgreSQL, SQLite nu necesită un proces server separat - se accesează direct din codul Python.

| Caracteristică     | SQLite                    | MySQL / PostgreSQL              |
| ------------------ | ------------------------- | ------------------------------- |
| Instalare          | Inclusă în Python         | Necesită instalare separată     |
| Fișier de date     | Un singur fișier `.db`    | Director de date complex        |
| Acces concurent    | Limitat (scrieri seriale)  | Optimizat pentru multe conexiuni|
| Potrivit pentru    | Prototipuri, aplicații mici| Aplicații de producție la scară |

SQLite este ideal pentru prototipuri și laboratoare, iar modulul `sqlite3` este inclus în Python - **nu necesită instalare**.

### 1.3 Configurarea conexiunii în FastAPI

Gestionarea corectă a conexiunilor la baza de date urmează același pattern pe care l-ați întâlnit în laboratorul precedent: **dependency injection**.

```python
import sqlite3

DATABASE = "sarcini.db"

def get_db():
    """Deschide o conexiune la baza de date și o închide automat după cerere."""
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # permite accesul la coloane cu nume (dict-like)
    try:
        conn.execute("PRAGMA foreign_keys = ON")  # activează verificarea cheilor externe
        yield conn
    finally:
        conn.close()
```

Câteva explicații:

- `check_same_thread=False` - SQLite restricționează implicit utilizarea aceleiași conexiuni din fire de execuție diferite. FastAPI poate rula handlere în fire diferite, deci această opțiune este necesară.
- `conn.row_factory = sqlite3.Row` - în mod implicit, SQLite returnează tupluri. Cu această setare, fiecare rând poate fi accesat ca un dicționar: `rand["coloana"]` în loc de `rand[0]`.
- `conn.execute("PRAGMA foreign_keys = ON")` - SQLite nu aplică constrângerile de cheie externă (`FOREIGN KEY`) implicit; această comandă activează verificarea pentru conexiunea curentă.
- `yield` - conexiunea rămâne deschisă pe durata procesării cererii și este **garantat** închisă după aceea, chiar și în caz de eroare.

> ⚠️ **Important:** Nu apelați `conn.close()` manual în handler. Funcția `get_db` se ocupă de acest lucru. Dacă faceți asta, veți obține erori la instrucțiunile executate ulterior în același handler.

---

## 2. CRUD complet cu SQLite

Vom construi un **gestionar de sarcini** (task manager) - o aplicație simplă în care utilizatorii autentificați pot gestiona o listă de sarcini personale.

### 2.1 Structura bazei de date

Aplicația va folosi două tabele:

```sql
-- Tabelul utilizatorilor
CREATE TABLE utilizatori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    parola_hash TEXT NOT NULL
);

-- Tabelul sarcinilor
CREATE TABLE sarcini (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titlu TEXT NOT NULL,
    descriere TEXT,
    finalizata INTEGER DEFAULT 0,         -- 0 = nefinalizată, 1 = finalizată
    utilizator_id INTEGER NOT NULL,
    FOREIGN KEY (utilizator_id) REFERENCES utilizatori(id)
);
```

Câmpul `finalizata` este de tip `INTEGER` (0 sau 1) deoarece SQLite nu are un tip de date boolean nativ. `FOREIGN KEY` declară relația dintre tabele: fiecare sarcină aparține unui utilizator.

> **Notă:** Constrângerile `FOREIGN KEY` în SQLite sunt declarate în schemă, dar verificarea lor este dezactivată implicit. Activarea se face prin `PRAGMA foreign_keys = ON` (adăugat în `get_db()` mai sus). Fără aceasta, SQLite acceptă valori `utilizator_id` care nu există în tabela `utilizatori`, fără nicio eroare.

### 2.2 Crearea automată a tabelelor la pornire

FastAPI oferă un mecanism de ciclu de viață (`lifespan`) care permite executarea de cod înainte ca aplicația să înceapă să accepte cereri:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
import sqlite3

DATABASE = "sarcini.db"

def initializeaza_db():
    """Creează tabelele dacă nu există deja."""
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS utilizatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            parola_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sarcini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titlu TEXT NOT NULL,
            descriere TEXT,
            finalizata INTEGER DEFAULT 0,
            utilizator_id INTEGER NOT NULL,
            FOREIGN KEY (utilizator_id) REFERENCES utilizatori(id)
        )
    """)
    conn.commit()
    conn.close()


@asynccontextmanager
async def durata_de_viata(app: FastAPI):
    initializeaza_db()   # se execută la pornire
    yield                # aplicația rulează și acceptă cereri
                         # (cod de curățare la oprire ar veni după yield)


app = FastAPI(title="Gestionar de sarcini", version="1.0.0", lifespan=durata_de_viata)
```

`CREATE TABLE IF NOT EXISTS` garantează că tabelele sunt create doar dacă nu există deja - comanda este sigur de rulat la oricâte reporniri.

### 2.3 Modelele de date

```python
from pydantic import BaseModel, Field
from typing import Optional


class SarcinaCreare(BaseModel):
    titlu: str = Field(min_length=1, max_length=200)
    descriere: Optional[str] = Field(default=None, max_length=1000)


class SarcinaActualizare(BaseModel):
    titlu: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descriere: Optional[str] = Field(default=None, max_length=1000)
    finalizata: Optional[bool] = None
```

Observați că `SarcinaActualizare` are toate câmpurile opționale - la o cerere PUT, clientul poate actualiza doar câmpurile dorite, celelalte rămânând neschimbate.

### 2.4 Endpoint-urile CRUD

#### Crearea unei sarcini (POST)

```python
@app.post("/sarcini", status_code=201)
def creeaza_sarcina(
    sarcina: SarcinaCreare,
    db: sqlite3.Connection = Depends(get_db),
):
    cursor = db.execute(
        "INSERT INTO sarcini (titlu, descriere, utilizator_id) VALUES (?, ?, ?)",
        (sarcina.titlu, sarcina.descriere, 1),  # utilizator_id hardcodat temporar
    )
    db.commit()
    sarcina_noua = db.execute(
        "SELECT * FROM sarcini WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return dict(sarcina_noua)
```

> ⚠️ **Important:** `db.commit()` este **obligatoriu** după orice operație de scriere (INSERT, UPDATE, DELETE). Fără `commit()`, modificările există doar temporar în memorie și se pierd la închiderea conexiunii - fără niciun mesaj de eroare.

`cursor.lastrowid` returnează ID-ul generat automat de `AUTOINCREMENT` pentru rândul tocmai inserat.

Parametrii `?` din șirul SQL sunt **parametri de substituție** (placeholders). Valorile sunt transmise separat ca o tuplă - metoda corectă de a include date variabile în interogări SQL.

> ⚠️ **Import - SQL Injection:** Codul de mai jos este **incorect și periculos**:
> ```python
> # NU FACEȚI AȘA
> db.execute(f"INSERT INTO sarcini (titlu) VALUES ('{sarcina.titlu}')")
> ```
> Un utilizator rău-intenționat ar putea trimite `titlu = "'; DROP TABLE sarcini; --"` și ar șterge toată baza de date. Folosiți întotdeauna parametrii `?`.

#### Citirea sarcinilor (GET)

```python
@app.get("/sarcini")
def obtine_sarcini(db: sqlite3.Connection = Depends(get_db)):
    sarcini = db.execute("SELECT * FROM sarcini").fetchall()
    return [dict(s) for s in sarcini]


@app.get("/sarcini/{sarcina_id}")
def obtine_sarcina(sarcina_id: int, db: sqlite3.Connection = Depends(get_db)):
    sarcina = db.execute(
        "SELECT * FROM sarcini WHERE id = ?", (sarcina_id,)
    ).fetchone()
    if not sarcina:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost găsită.")
    return dict(sarcina)
```

`fetchall()` returnează o listă de rânduri; `fetchone()` returnează primul rând găsit sau `None`.

`dict(sarcina)` convertește un obiect `sqlite3.Row` (care se comportă ca un dicționar) într-un dicționar Python standard, pe care FastAPI îl poate serializa automat în JSON.

#### Actualizarea unei sarcini (PUT)

```python
@app.put("/sarcini/{sarcina_id}")
def actualizeaza_sarcina(
    sarcina_id: int,
    date: SarcinaActualizare,
    db: sqlite3.Connection = Depends(get_db),
):
    sarcina = db.execute(
        "SELECT * FROM sarcini WHERE id = ?", (sarcina_id,)
    ).fetchone()
    if not sarcina:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost găsită.")

    sarcina_dict = dict(sarcina)
    titlu_nou = date.titlu if date.titlu is not None else sarcina_dict["titlu"]
    descriere_noua = date.descriere if date.descriere is not None else sarcina_dict["descriere"]
    finalizata_noua = int(date.finalizata) if date.finalizata is not None else sarcina_dict["finalizata"]

    db.execute(
        "UPDATE sarcini SET titlu = ?, descriere = ?, finalizata = ? WHERE id = ?",
        (titlu_nou, descriere_noua, finalizata_noua, sarcina_id),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM sarcini WHERE id = ?", (sarcina_id,)).fetchone())
```

Logica `valoare_noua if valoare_noua is not None else valoare_veche` implementează actualizarea parțială: câmpurile netrimise de client rămân neschimbate.

#### Ștergerea unei sarcini (DELETE)

```python
@app.delete("/sarcini/{sarcina_id}")
def sterge_sarcina(sarcina_id: int, db: sqlite3.Connection = Depends(get_db)):
    sarcina = db.execute(
        "SELECT * FROM sarcini WHERE id = ?", (sarcina_id,)
    ).fetchone()
    if not sarcina:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost găsită.")

    db.execute("DELETE FROM sarcini WHERE id = ?", (sarcina_id,))
    db.commit()
    return {"mesaj": f"Sarcina cu ID-ul {sarcina_id} a fost ștearsă."}
```

---

## 3. Autentificarea utilizatorilor

### 3.1 De ce avem nevoie de autentificare

Implementarea CRUD de mai sus are o problemă: oricine poate accesa și modifica orice sarcină. Într-o aplicație reală, fiecare utilizator trebuie să vadă și să modifice **doar propriile date**.

**Autentificarea** (authentication) răspunde la întrebarea *„Cine ești?"*, iar **autorizarea** (authorization) răspunde la *„Ce ai voie să faci?"*. Laboratorul de față acoperă autentificarea; autorizarea granulară (roluri, permisiuni) depășește scopul unui MVP.

### 3.2 Stocarea securizată a parolelor

Parolele nu se stochează niciodată în text clar (plaintext). Dacă baza de date ar fi compromisă, atacatorul ar obține direct parolele tuturor utilizatorilor - parole pe care aceștia le-ar putea folosi și pe alte servicii.

Soluția este **hashing-ul criptografic**: o funcție matematică unidirecțională care transformă parola într-un șir de caractere de lungime fixă. Nu există o modalitate practică de a obține parola originală din hash.

**bcrypt** este algoritmul recomandat pentru parole: este deliberat lent (pentru a îngreuna atacurile prin forță brută) și include un **salt** aleator (pentru a preveni atacurile cu tabele precomputate - *rainbow tables*).

```python
from passlib.context import CryptContext

context_parola = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hasheaza_parola(parola: str) -> str:
    return context_parola.hash(parola)


def verifica_parola(parola: str, hash_parola: str) -> bool:
    return context_parola.verify(parola, hash_parola)
```

> ⚠️ **Important:** Pe unele sisteme, instalarea `passlib[bcrypt]` poate necesita și pachetul `bcrypt` instalat explicit. Dacă apare eroarea `ModuleNotFoundError: No module named 'bcrypt'`, rulați `pip install bcrypt`.

### 3.3 JSON Web Tokens (JWT)

**JWT** (JSON Web Token, RFC 7519) este un standard pentru transmiterea securizată a informațiilor între două entități. Un token JWT este un șir de text cu trei componente separate prin punct:

```
eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyQGV4LmNvbSJ9.abc123
     HEADER                      PAYLOAD                SEM­NĂ­TU­RĂ
```

- **Header** - specifică tipul tokenului și algoritmul de semnare, encodat Base64URL;
- **Payload** - datele utile (ex.: email-ul utilizatorului, data expirării), encodat Base64URL;
- **Semnătura** - calculată din header și payload folosind o cheie secretă deținută doar de server.

> **Important:** Payload-ul JWT este encodat **Base64URL**, **nu criptat**. Oricine poate decoda și citi conținutul. Semnătura garantează doar că tokenul nu a fost modificat după emitere. Nu stocați date sensibile (parole, numere de card) în payload.
>
> *Base64URL* este o variantă a encodării Base64 care înlocuiește `+` cu `-` și `/` cu `_`, eliminând și caracterul de padding `=` - pentru a fi sigur de utilizat în URL-uri și headere HTTP.

Fluxul de autentificare cu JWT:

```
1. Client → POST /autentificare  { email, parola }
2. Server verifică credențialele și generează un token JWT semnat
3. Server → Client               { access_token: "eyJ..." }
4. Client → GET /sarcini         + header: Authorization: Bearer eyJ...
5. Server validează semnătura tokenului și procesează cererea
```

### 3.4 Implementarea JWT

Instalați dependențele noi în mediul virtual activ:

```bash
pip install PyJWT passlib[bcrypt]
```

Actualizați `requirements.txt`:

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
```

> ⚠️ **Important:** Pachetul se instalează cu `pip install PyJWT`, dar se importă în Python ca `import jwt` (fără majusculele `Py`). Nu confundați cu pachetul abandonat `jwt` (litere mici), care este diferit.

Configurarea și funcțiile JWT:

```python
import jwt
from datetime import datetime, timedelta, timezone

SECRET_KEY = "cheie-secreta-foarte-lunga-schimbati-obligatoriu-in-productie"
ALGORITHM = "HS256"
EXPIRARE_TOKEN_MINUTE = 30


def creeaza_token(date: dict) -> str:
    """Generează un token JWT cu data de expirare inclusă."""
    date_copie = date.copy()
    date_copie["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRARE_TOKEN_MINUTE)
    return jwt.encode(date_copie, SECRET_KEY, algorithm=ALGORITHM)
```

> ⚠️ **Important - securitate:** `SECRET_KEY` hardcodat în codul sursă este o problemă gravă dacă proiectul ajunge pe GitHub sau alt repository public. Într-o aplicație reală, aceasta se citește dintr-o variabilă de mediu: `SECRET_KEY = os.environ.get("SECRET_KEY", "valoare-implicita-doar-pentru-dev")`. Pentru laborator, valoarea hardcodată este acceptabilă.

> ⚠️ **Important:** S-a ales JWT local deoarece Google Sign-In (conectarea folosind un buton Google) necesită crearea unui Google Cloud Project cu verificare de cont (posibil card de credit/debit) și numeroși pași de configurare. JWT local nu necesită niciun serviciu extern.

### 3.5 Endpoint-urile de autentificare

Modelul de date pentru înregistrare, cu validare inclusă:

```python
from pydantic import BaseModel, Field, field_validator


class UtilizatorInregistrare(BaseModel):
    email: str = Field(min_length=5, max_length=100)
    parola: str = Field(min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Adresa de email nu este validă.")
        return v.lower()  # normalizare: stocăm email-ul cu litere mici
```

Endpoint-ul de înregistrare:

```python
@app.post("/inregistrare", status_code=201)
def inregistrare(utilizator: UtilizatorInregistrare, db: sqlite3.Connection = Depends(get_db)):
    existent = db.execute(
        "SELECT id FROM utilizatori WHERE email = ?", (utilizator.email,)
    ).fetchone()
    if existent:
        raise HTTPException(status_code=400, detail="Adresa de email este deja înregistrată.")

    db.execute(
        "INSERT INTO utilizatori (email, parola_hash) VALUES (?, ?)",
        (utilizator.email, hasheaza_parola(utilizator.parola)),
    )
    db.commit()
    return {"mesaj": f"Utilizatorul {utilizator.email} a fost înregistrat cu succes."}
```

Endpoint-ul de autentificare folosește `OAuth2PasswordRequestForm` - un formular standard OAuth2 cu câmpurile `username` și `password`:

```python
from fastapi.security import OAuth2PasswordRequestForm


@app.post("/autentificare")
def autentificare(
    formular: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db),
):
    utilizator = db.execute(
        "SELECT * FROM utilizatori WHERE email = ?", (formular.username,)
    ).fetchone()
    if not utilizator or not verifica_parola(formular.password, utilizator["parola_hash"]):
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă.")

    token = creeaza_token({"sub": utilizator["email"]})
    return {"access_token": token, "token_type": "bearer"}
```

> **Notă:** `OAuth2PasswordRequestForm` folosește câmpul `username`, nu `email` - acesta este un standard OAuth2. Vom folosi adresa de email drept valoare pentru `username`.

Eroarea `401 Unauthorized` are în mod intenționat același mesaj indiferent dacă email-ul nu există sau parola este greșită. Mesaje diferite ar permite unui atacator să afle ce adrese de email sunt înregistrate în sistem (**enumerarea utilizatorilor**).

---

## 4. Protejarea endpoint-urilor

### 4.1 Extragerea utilizatorului curent

FastAPI oferă clasa `OAuth2PasswordBearer` care extrage automat token-ul din headerul `Authorization: Bearer <token>`:

```python
from fastapi.security import OAuth2PasswordBearer

oauth2_schema = OAuth2PasswordBearer(tokenUrl="autentificare")
```

`tokenUrl="autentificare"` specifică endpoint-ul de autentificare - Swagger UI îl folosește pentru a știi unde să trimită credențialele atunci când apăsați butonul **Authorize**.

Funcția de dependență care validează tokenul și returnează utilizatorul autentificat:

```python
def get_utilizator_curent(
    token: str = Depends(oauth2_schema),
    db: sqlite3.Connection = Depends(get_db),
):
    """Extrage și validează token-ul JWT; returnează utilizatorul autentificat."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalid.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirat. Autentificați-vă din nou.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalid.")

    utilizator = db.execute(
        "SELECT * FROM utilizatori WHERE email = ?", (email,)
    ).fetchone()
    if not utilizator:
        raise HTTPException(status_code=401, detail="Utilizatorul nu există.")
    return utilizator
```

### 4.2 Aplicarea protecției

Adăugând `Depends(get_utilizator_curent)` la un endpoint, acesta devine accesibil **doar utilizatorilor autentificați**. Dacă o cerere ajunge fără token sau cu un token invalid, FastAPI returnează automat `401 Unauthorized` înainte ca handler-ul să fie executat.

```python
@app.get("/sarcini")
def obtine_sarcini(
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    sarcini = db.execute(
        "SELECT * FROM sarcini WHERE utilizator_id = ?", (utilizator_curent["id"],)
    ).fetchall()
    return [dict(s) for s in sarcini]
```

Observați că filtrăm sarcinile după `utilizator_id = ?` - fiecare utilizator vede **exclusiv sarcinile proprii**, chiar dacă ghicește ID-ul unei sarcini aparținând altcuiva.

---

## 5. Validare API avansată

### 5.1 Restricții cu `Field`

`Field` din Pydantic permite declararea restricțiilor direct pe câmpuri, fără cod suplimentar:

```python
from pydantic import BaseModel, Field

class SarcinaCreare(BaseModel):
    titlu: str = Field(min_length=1, max_length=200, description="Titlul sarcinii")
    descriere: str | None = Field(default=None, max_length=1000)
```

Câteva restricții utile:

| Parametru    | Tipuri aplicabile | Efect                               |
| ------------ | ----------------- | ----------------------------------- |
| `min_length` | `str`             | Lungime minimă                      |
| `max_length` | `str`             | Lungime maximă                      |
| `gt`, `ge`   | numere            | Mai mare decât / mai mare sau egal  |
| `lt`, `le`   | numere            | Mai mic decât / mai mic sau egal    |
| `pattern`    | `str`             | Trebuie să respecte un regex        |

### 5.2 Validatori personalizați cu `@field_validator`

Pentru validări care nu pot fi exprimate prin parametrii `Field`, se definesc metode decorate cu `@field_validator`:

```python
from pydantic import BaseModel, Field, field_validator


class UtilizatorInregistrare(BaseModel):
    email: str = Field(min_length=5, max_length=100)
    parola: str = Field(min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Adresa de email nu este validă.")
        return v.lower()
```

`@classmethod` este necesar - validatorii Pydantic v2 sunt metode de clasă, nu metode de instanță. Ridicarea unui `ValueError` produce automat un răspuns `422 Unprocessable Entity` cu mesajul specificat, vizibil în Swagger UI.

---

## 6. Securitate vs funcționalitate

Implementarea securității implică întotdeauna compromisuri între gradul de protecție și ușurința de utilizare. Câteva situații frecvente:

### Expirarea token-urilor

Un token JWT fără expirare este convenabil (utilizatorul nu trebuie să se reautentifice), dar dacă este furat, atacatorul are acces permanent. Un token cu expirare scurtă (30 minute) limitează fereastra de atac, dar poate frustra utilizatorii.

**MVP minim acceptabil:** expirare de 24–72 ore pentru aplicații interne, 15–30 minute pentru aplicații cu date sensibile.

### Mesajele de eroare

```python
# Prea informativ - facilitează enumerarea utilizatorilor
raise HTTPException(status_code=401, detail="Parola incorectă pentru acest email.")

# Corect - nu dezvăluie dacă email-ul există în sistem
raise HTTPException(status_code=401, detail="Email sau parolă incorectă.")
```

### CORS (Cross-Origin Resource Sharing)

Dacă un frontend web (rulând pe `http://localhost:3000`) încearcă să apeleze API-ul (pe `http://localhost:8000`), browserul blochează cererea din motive de securitate (politica Same-Origin). FastAPI include middleware CORS:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # în producție, specificați exact originile permise
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> ⚠️ `allow_origins=["*"]` permite cereri din orice sursă - convenabil în dezvoltare, **inadmisibil în producție** pentru aplicații cu autentificare, deoarece permite oricărui site web să trimită cereri către API-ul vostru din browserul unui utilizator autentificat.

### Ce este obligatoriu vs opțional pentru MVP

| Măsură de securitate     | MVP obligatoriu? | Motiv                                              |
| ------------------------ | ---------------- | -------------------------------------------------- |
| Parole hashate (bcrypt)  | Da               | Date compromise → irecuperabil                     |
| Expirare token JWT       | Da               | Token furat → acces permanent fără expirare        |
| HTTPS                    | Da (producție)   | Tokenurile se transmit în clar pe HTTP             |
| Rate limiting            | Nu (MVP)         | Util, dar adaugă complexitate semnificativă        |
| Refresh tokens           | Nu (MVP)         | Îmbunătățesc UX, dar complică implementarea        |
| Logging și audit         | Nu (MVP)         | Util pentru debugging și conformitate              |

---

## 7. Aplicația completă

Mai jos este codul complet al aplicației, care integrează toate conceptele prezentate. Salvați-l ca `main.py` și porniți serverul cu `uvicorn main:app --reload`.

```python
import sqlite3
import jwt
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Configurare
# ---------------------------------------------------------------------------

DATABASE = "sarcini.db"
SECRET_KEY = "cheie-secreta-foarte-lunga-schimbati-obligatoriu-in-productie"
ALGORITHM = "HS256"
EXPIRARE_TOKEN_MINUTE = 30

context_parola = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_schema = OAuth2PasswordBearer(tokenUrl="autentificare")


# ---------------------------------------------------------------------------
# Baza de date
# ---------------------------------------------------------------------------

def initializeaza_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS utilizatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            parola_hash TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sarcini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titlu TEXT NOT NULL,
            descriere TEXT,
            finalizata INTEGER DEFAULT 0,
            utilizator_id INTEGER NOT NULL,
            FOREIGN KEY (utilizator_id) REFERENCES utilizatori(id)
        )
    """)
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        yield conn
    finally:
        conn.close()


@asynccontextmanager
async def durata_de_viata(app: FastAPI):
    initializeaza_db()
    yield


# ---------------------------------------------------------------------------
# Aplicația
# ---------------------------------------------------------------------------

app = FastAPI(title="Gestionar de sarcini", version="1.0.0", lifespan=durata_de_viata)


# ---------------------------------------------------------------------------
# Modele Pydantic
# ---------------------------------------------------------------------------

class UtilizatorInregistrare(BaseModel):
    email: str = Field(min_length=5, max_length=100)
    parola: str = Field(min_length=8, max_length=100)

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Adresa de email nu este validă.")
        return v.lower()


class SarcinaCreare(BaseModel):
    titlu: str = Field(min_length=1, max_length=200)
    descriere: Optional[str] = Field(default=None, max_length=1000)


class SarcinaActualizare(BaseModel):
    titlu: Optional[str] = Field(default=None, min_length=1, max_length=200)
    descriere: Optional[str] = Field(default=None, max_length=1000)
    finalizata: Optional[bool] = None


# ---------------------------------------------------------------------------
# Funcții utilitare
# ---------------------------------------------------------------------------

def hasheaza_parola(parola: str) -> str:
    return context_parola.hash(parola)


def verifica_parola(parola: str, hash_parola: str) -> bool:
    return context_parola.verify(parola, hash_parola)


def creeaza_token(date: dict) -> str:
    date_copie = date.copy()
    date_copie["exp"] = datetime.now(timezone.utc) + timedelta(minutes=EXPIRARE_TOKEN_MINUTE)
    return jwt.encode(date_copie, SECRET_KEY, algorithm=ALGORITHM)


def get_utilizator_curent(
    token: str = Depends(oauth2_schema),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Token invalid.")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirat. Autentificați-vă din nou.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalid.")

    utilizator = db.execute(
        "SELECT * FROM utilizatori WHERE email = ?", (email,)
    ).fetchone()
    if not utilizator:
        raise HTTPException(status_code=401, detail="Utilizatorul nu există.")
    return utilizator


# ---------------------------------------------------------------------------
# Endpoint-uri: autentificare
# ---------------------------------------------------------------------------

@app.post("/inregistrare", status_code=201)
def inregistrare(utilizator: UtilizatorInregistrare, db: sqlite3.Connection = Depends(get_db)):
    existent = db.execute(
        "SELECT id FROM utilizatori WHERE email = ?", (utilizator.email,)
    ).fetchone()
    if existent:
        raise HTTPException(status_code=400, detail="Adresa de email este deja înregistrată.")

    db.execute(
        "INSERT INTO utilizatori (email, parola_hash) VALUES (?, ?)",
        (utilizator.email, hasheaza_parola(utilizator.parola)),
    )
    db.commit()
    return {"mesaj": f"Utilizatorul {utilizator.email} a fost înregistrat cu succes."}


@app.post("/autentificare")
def autentificare(
    formular: OAuth2PasswordRequestForm = Depends(),
    db: sqlite3.Connection = Depends(get_db),
):
    utilizator = db.execute(
        "SELECT * FROM utilizatori WHERE email = ?", (formular.username,)
    ).fetchone()
    if not utilizator or not verifica_parola(formular.password, utilizator["parola_hash"]):
        raise HTTPException(status_code=401, detail="Email sau parolă incorectă.")

    token = creeaza_token({"sub": utilizator["email"]})
    return {"access_token": token, "token_type": "bearer"}


# ---------------------------------------------------------------------------
# Endpoint-uri: sarcini (protejate cu JWT)
# ---------------------------------------------------------------------------

@app.get("/sarcini")
def obtine_sarcini(
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    sarcini = db.execute(
        "SELECT * FROM sarcini WHERE utilizator_id = ?", (utilizator_curent["id"],)
    ).fetchall()
    return [dict(s) for s in sarcini]


@app.get("/sarcini/{sarcina_id}")
def obtine_sarcina(
    sarcina_id: int,
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    sarcina = db.execute(
        "SELECT * FROM sarcini WHERE id = ? AND utilizator_id = ?",
        (sarcina_id, utilizator_curent["id"]),
    ).fetchone()
    if not sarcina:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost găsită.")
    return dict(sarcina)


@app.post("/sarcini", status_code=201)
def creeaza_sarcina(
    sarcina: SarcinaCreare,
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    cursor = db.execute(
        "INSERT INTO sarcini (titlu, descriere, utilizator_id) VALUES (?, ?, ?)",
        (sarcina.titlu, sarcina.descriere, utilizator_curent["id"]),
    )
    db.commit()
    sarcina_noua = db.execute(
        "SELECT * FROM sarcini WHERE id = ?", (cursor.lastrowid,)
    ).fetchone()
    return dict(sarcina_noua)


@app.put("/sarcini/{sarcina_id}")
def actualizeaza_sarcina(
    sarcina_id: int,
    date: SarcinaActualizare,
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    sarcina = db.execute(
        "SELECT * FROM sarcini WHERE id = ? AND utilizator_id = ?",
        (sarcina_id, utilizator_curent["id"]),
    ).fetchone()
    if not sarcina:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost găsită.")

    sarcina_dict = dict(sarcina)
    titlu_nou = date.titlu if date.titlu is not None else sarcina_dict["titlu"]
    descriere_noua = date.descriere if date.descriere is not None else sarcina_dict["descriere"]
    finalizata_noua = int(date.finalizata) if date.finalizata is not None else sarcina_dict["finalizata"]

    db.execute(
        "UPDATE sarcini SET titlu = ?, descriere = ?, finalizata = ? WHERE id = ?",
        (titlu_nou, descriere_noua, finalizata_noua, sarcina_id),
    )
    db.commit()
    return dict(db.execute("SELECT * FROM sarcini WHERE id = ?", (sarcina_id,)).fetchone())


@app.delete("/sarcini/{sarcina_id}")
def sterge_sarcina(
    sarcina_id: int,
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    sarcina = db.execute(
        "SELECT * FROM sarcini WHERE id = ? AND utilizator_id = ?",
        (sarcina_id, utilizator_curent["id"]),
    ).fetchone()
    if not sarcina:
        raise HTTPException(status_code=404, detail="Sarcina nu a fost găsită.")

    db.execute("DELETE FROM sarcini WHERE id = ?", (sarcina_id,))
    db.commit()
    return {"mesaj": f"Sarcina cu ID-ul {sarcina_id} a fost ștearsă."}
```

### 7.1 Testarea prin Swagger UI

Porniți serverul și accesați `http://127.0.0.1:8000/docs`.

**Fluxul de test recomandat:**

1. `POST /inregistrare` - creați un cont cu email și parolă;
2. Apăsați butonul **Authorize** (iconița lacăt din dreapta sus);
3. Introduceți email-ul în câmpul `username` și parola în câmpul `password`, apăsați **Authorize**;
4. Swagger UI apelează automat `POST /autentificare` și reține token-ul JWT;
5. Testați `POST /sarcini`, `GET /sarcini`, `PUT /sarcini/{id}`, `DELETE /sarcini/{id}`.

> **Notă:** Dacă primiți `401 Unauthorized` deși v-ați autentificat, token-ul a expirat (după 30 de minute). Apăsați **Authorize** → **Logout** → **Authorize** din nou.

---

## 8. Exercițiu practic: extinderea gestinarului de sarcini

### 8.1 Cerințe

Pornind de la codul complet din secțiunea anterioară, implementați următoarele două funcționalități:

**A. Endpoint de finalizare rapidă**

Adăugați endpoint-ul `PATCH /sarcini/{sarcina_id}/finalizeaza` care marchează o sarcină ca finalizată fără a necesita un corp al cererii. Endpoint-ul trebuie să fie protejat cu JWT și să returneze sarcina actualizată.

**B. Filtrarea sarcinilor după stare**

Modificați endpoint-ul `GET /sarcini` astfel încât să accepte un parametru de interogare opțional `doar_nefinalizate: bool = False`. Când parametrul este `true`, endpoint-ul returnează **doar** sarcinile cu `finalizata = 0`.

### 8.2 Tabel de endpoint-uri după implementare

| Metodă  | Cale                             | Protejat | Descriere                          |
| ------- | -------------------------------- | -------- | ---------------------------------- |
| `POST`  | `/inregistrare`                  | Nu       | Creare cont utilizator             |
| `POST`  | `/autentificare`                 | Nu       | Obținere token JWT                 |
| `GET`   | `/sarcini`                       | Da       | Lista sarcinilor (cu filtrare)     |
| `GET`   | `/sarcini/{id}`                  | Da       | Detalii sarcină                    |
| `POST`  | `/sarcini`                       | Da       | Creare sarcină nouă                |
| `PUT`   | `/sarcini/{id}`                  | Da       | Actualizare sarcină                |
| `PATCH` | `/sarcini/{id}/finalizeaza`      | Da       | Marcare sarcină ca finalizată      |
| `DELETE`| `/sarcini/{id}`                  | Da       | Ștergere sarcină                   |

### 8.3 Cod de pornire

```python
# Adăugați acest endpoint în main.py, alături de celelalte endpoint-uri de sarcini

@app.patch("/sarcini/{sarcina_id}/finalizeaza")
def finalizeaza_sarcina(
    sarcina_id: int,
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    # TODO: Verificați că sarcina există și aparține utilizatorului curent
    # (returnați 404 dacă nu este găsită)

    # TODO: Actualizați câmpul finalizata la 1 în baza de date
    # (nu uitați db.commit())

    # TODO: Returnați sarcina actualizată ca dicționar
    pass


# Modificați endpoint-ul existent GET /sarcini astfel:

@app.get("/sarcini")
def obtine_sarcini(
    doar_nefinalizate: bool = False,  # parametru de interogare nou
    db: sqlite3.Connection = Depends(get_db),
    utilizator_curent=Depends(get_utilizator_curent),
):
    # TODO: Dacă doar_nefinalizate este True, adăugați condiția
    # "AND finalizata = 0" la interogarea SQL
    # Hint: puteți construi interogarea ca șir de caractere sau
    # puteți face două apeluri db.execute() separate (câte unul pentru fiecare caz)
    pass
```

### 8.4 Indicații

- Endpoint-ul PATCH nu primește niciun corp - are nevoie doar de `sarcina_id` din cale și de utilizatorul curent din token.
- Verificați că un utilizator **nu poate finaliza** sarcinile altui utilizator (filtrul `AND utilizator_id = ?` trebuie să fie prezent).
- Testați filtrarea: creați două sarcini, finalizați-o pe una cu `PATCH /sarcini/{id}/finalizeaza`, apoi apelați `GET /sarcini?doar_nefinalizate=true` și verificați că apare doar sarcina nefinalizată.

### 8.5 Extindere opțională (bonus)

- Adăugați un câmp `data_crearii TEXT` la tabela `sarcini`, populat automat cu `datetime.now().isoformat()` la INSERT.
- Adăugați endpoint-ul `GET /utilizatori/eu` care returnează informații despre utilizatorul autentificat (fără câmpul `parola_hash`).

---

## Referințe

- [Documentația oficială FastAPI - Security](https://fastapi.tiangolo.com/tutorial/security/)
- [Documentația PyJWT](https://pyjwt.readthedocs.io/)
- [Documentația passlib](https://passlib.readthedocs.io/)
- [Documentația modulului sqlite3 (Python)](https://docs.python.org/3/library/sqlite3.html)
- [RFC 7519 - JSON Web Token](https://datatracker.ietf.org/doc/html/rfc7519) (specificația oficială JWT)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
