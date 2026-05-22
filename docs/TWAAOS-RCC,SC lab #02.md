# Laborator 2: Introducere în serviciile web cu FastAPI

## Obiective

La finalul acestui laborator, studentul va fi capabil să:

- explice ciclul cerere-răspuns (request-response cycle) al protocolului HTTP;
- identifice metodele HTTP și codurile de stare (status codes) utilizate frecvent în serviciile web;
- configureze un mediu de lucru Python izolat pentru un proiect FastAPI;
- definească endpoint-uri simple care răspund la cereri GET, POST și DELETE;
- valideze date de intrare folosind modele Pydantic;
- testeze manual un serviciu web prin interfața Swagger UI.

---

## 1. Ce este un serviciu web?

Un **serviciu web** (*web service*) este o aplicație care rulează pe un server și expune funcționalități accesibile prin rețea, folosind protocolul HTTP. Spre deosebire de o aplicație web clasică ce returnează pagini HTML pentru a fi afișate într-un browser, un serviciu web returnează de regulă date structurate — cel mai adesea în format JSON — destinate a fi consumate de alte aplicații (clienți mobili, aplicații frontend, alte servicii etc.).

Arhitectura pe care o vom studia se numește **REST** (**Re**presentational **S**tate **T**ransfer). REST nu este un protocol, ci un set de principii arhitecturale care descriu cum trebuie să se comporte un serviciu web pentru a fi predictibil, scalabil și ușor de integrat.

### 1.1 Modelul client-server

Orice comunicare HTTP implică doi participanți:

- **Clientul** (client) — inițiază comunicarea trimițând o cerere (request). Poate fi un browser, o aplicație mobilă sau un alt serviciu.
- **Serverul** (server) — primește cererea, o procesează și trimite înapoi un răspuns (response).

Această separare clară a responsabilităților este unul dintre principiile fundamentale ale REST: clientul nu știe nimic despre implementarea internă a serverului, iar serverul nu păstrează starea clientului între cereri (principiul **stateless**).

### 1.2 Anatomia unui apel URL

Un URL (Uniform Resource Locator) identifică unic o resursă de pe server. Structura sa este:

```
https://api.exemplu.ro:8000/produse/42?detaliat=true
│       │             │    │          └─ query string
│       │             │    └─ cale (path)
│       │             └─ port
│       └─ gazdă (host)
└─ schemă (scheme)
```

În contextul REST, URL-ul identifică o **resursă** (resource) — un concept din domeniul problemei (un produs, un utilizator, o comandă), nu o acțiune. Acțiunea este exprimată prin metoda HTTP, nu prin URL.

| Corect (REST)        | Incorect                      |
| -------------------- | ----------------------------- |
| `DELETE /produse/42` | `POST /sterge-produs/42`      |
| `GET /utilizatori/7` | `GET /obtine-utilizator?id=7` |

### 1.3 Ciclul cerere-răspuns (request-response cycle)

O cerere HTTP conține:

- **Metoda** (method) — acțiunea solicitată (GET, POST, PUT, DELETE etc.);
- **Calea** (path) — resursa vizată (`/produse/42`);
- **Anteturi** (headers) — metadate despre cerere (`Content-Type`, `Authorization` etc.);
- **Corpul** (body) — date trimise serverului, prezente de regulă la POST și PUT.

Un răspuns HTTP conține:

- **Codul de stare** (status code) — un număr din trei cifre care indică rezultatul;
- **Anteturi** (headers) — metadate despre răspuns;
- **Corpul** (body) — datele returnate, de regulă JSON.

### 1.4 Metode HTTP

| Metodă   | Utilizare tipică                    | Are corp (*body*)? |
| -------- | ----------------------------------- | ------------------ |
| `GET`    | Citirea unei resurse                | Nu                 |
| `POST`   | Crearea unei resurse noi            | Da                 |
| `PUT`    | Înlocuirea completă a unei resurse  | Da                 |
| `PATCH`  | Modificarea parțială a unei resurse | Da                 |
| `DELETE` | Ștergerea unei resurse              | Nu (opțional)      |

### 1.5 Coduri de stare HTTP

Codurile de stare sunt grupate în cinci clase:

| Clasă          | Interval | Semnificație                             |
| -------------- | -------- | ---------------------------------------- |
| Succes         | 2xx      | Cererea a fost procesată cu succes       |
| Redirecționare | 3xx      | Resursa s-a mutat                        |
| Eroare client  | 4xx      | Cererea este greșită sau neautorizată    |
| Eroare server  | 5xx      | Serverul a întâmpinat o problemă internă |

Cele mai frecvente coduri pe care le veți folosi:

| Cod                         | Nume                   | Când se folosește                             |
| --------------------------- | ---------------------- | --------------------------------------------- |
| `200 OK`                    | Succes                 | Răspuns la GET, PUT, PATCH, DELETE reușite    |
| `201 Created`               | Creat                  | Răspuns la POST când resursa a fost creată    |
| `400 Bad Request`           | Cerere invalidă        | Date de intrare incorecte sau lipsă           |
| `404 Not Found`             | Negăsit                | Resursa nu există                             |
| `422 Unprocessable Entity`  | Entitate neprocesabilă | Validare eșuată (folosit implicit de FastAPI) |
| `500 Internal Server Error` | Eroare internă         | Eroare neașteptată pe server                  |

---

## 2. Pregătirea mediului de lucru

### 2.1 Mediul virtual (virtual environment)

Fiecare proiect Python ar trebui să ruleze într-un **mediu virtual** (virtual environment) — un director izolat care conține o copie a interpretorului Python și pachetele instalate exclusiv pentru acel proiect. Astfel se evită conflictele de versiuni între proiecte diferite.

```bash
# Crearea mediului virtual
python3 -m venv venv

# Activarea mediului (Linux / macOS)
source venv/bin/activate

# Verificarea activării — promptul terminalului se va schimba
# (venv) user@host:~/proiect$
```

> **Notă:** Odată activat mediul virtual, toate comenzile `pip install` vor instala pachetele exclusiv în acel mediu, fără a afecta sistemul.

### 2.2 Fișierul de dependențe

Creați un fișier `requirements.txt` în directorul proiectului:

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
```

Instalați dependențele:

```bash
pip install -r requirements.txt
```

> **Notă**: Alternativ, se pot instala individual dependințele (`fastapi`, `uvicorn[standard]` și `pydantic`), apoi acestea se scriu în fișierul `requirements.txt`:
> 
> `pip freeze > requirements.txt`

### 2.3 Serverul ASGI și Uvicorn

FastAPI este un framework **asincron** (asynchronous), ceea ce înseamnă că nu rulează printr-un server clasic WSGI (precum Gunicorn în configurație de bază), ci printr-un server **ASGI** (Asynchronous Server Gateway Interface). Uvicorn este implementarea ASGI standard pentru FastAPI.

Comanda de pornire a serverului:

```bash
uvicorn main:app --reload
```

- `main` — numele fișierului Python (`main.py`) fără extensie;
- `app` — numele variabilei de tip `FastAPI` din acel fișier;
- `--reload` — serverul repornește automat la fiecare modificare a codului sursă. **Folosiți această opțiune exclusiv în dezvoltare**, nu în producție.

---

## 3. Primul serviciu web

### 3.1 Structura de bază

Creați fișierul `main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="Serviciu de demonstrație", version="1.0.0")


@app.get("/")
def radacina():
    """Endpoint de verificare a stării serviciului."""
    return {"status": "activ"}
```

Porniți serverul și accesați `http://127.0.0.1:8000/` într-un browser sau din terminal:

```bash
curl http://127.0.0.1:8000/
# {"status":"activ"}
```

### 3.2 Parametri de cale (path parameters)

Un **parametru de cale** (path parameter) face parte din URL și identifică o resursă specifică. Se declară între acolade în decorator și ca argument al funcției:

```python
@app.get("/utilizatori/{user_id}")
def obtine_utilizator(user_id: int):
    return {"id": user_id, "mesaj": f"Utilizatorul cu ID-ul {user_id}"}
```

FastAPI validează automat tipul: dacă `user_id` nu poate fi convertit la `int`, serverul va returna `422 Unprocessable Entity`.

### 3.3 Parametri de interogare (query parameters)

**Parametrii de interogare** (query parameters) sunt perechi cheie-valoare adăugate după semnul `?` în URL. Se declară ca argumente ale funcției care nu apar în calea endpoint-ului:

```python
@app.get("/produse")
def lista_produse(pagina: int = 1, per_pagina: int = 10):
    return {
        "pagina": pagina,
        "per_pagina": per_pagina,
        "mesaj": f"Returnează produsele de pe pagina {pagina}"
    }
```

Apel exemplu: `GET /produse?pagina=2&per_pagina=5`

Argumentele cu valori implicite sunt opționale. Cele fără valori implicite sunt obligatorii.

### 3.4 Interfața Swagger UI

FastAPI generează automat documentație interactivă pentru toate endpoint-urile definite. Accesați `http://127.0.0.1:8000/docs` în browser.

Swagger UI vă permite să:

- vizualizați toate endpoint-urile disponibile, metodele și parametrii acestora;
- trimiteți cereri de test direct din browser, fără a folosi un client extern;
- inspectați structura răspunsurilor așteptate.

Aceasta este o unealtă esențială în dezvoltarea și depanarea (debugging) unui serviciu web.

---

## 4. Validarea datelor cu Pydantic

### 4.1 Necesitatea validării

Când un client trimite date printr-o cerere POST sau PUT, nu putem presupune că acestea sunt corecte sau complete. Validarea manuală este verbosă și predispusă la erori. **Pydantic** rezolvă această problemă prin declararea unui **model de date** (data model) — o clasă Python cu sugestii de tip (type hints) din care Pydantic generează automat logica de validare.

### 4.2 Definirea unui model

Un model Pydantic moștenește clasa `BaseModel`:

```python
from pydantic import BaseModel


class Produs(BaseModel):
    id: int
    nume: str
    pret: float
    stoc: int
```

Dacă un câmp este opțional sau are o valoare implicită:

```python
from pydantic import BaseModel


class Produs(BaseModel):
    id: int
    nume: str
    pret: float
    stoc: int = 0          # valoare implicită
    descriere: str | None = None   # câmp opțional
```

### 4.3 Endpoint POST cu model Pydantic

Declarați modelul ca parametru al funcției handler. FastAPI va extrage și valida automat datele din corpul cererii:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


class Produs(BaseModel):
    id: int
    nume: str
    pret: float
    stoc: int = 0


inventar: list[Produs] = []


@app.post("/produse", status_code=201)
def adauga_produs(produs: Produs):
    inventar.append(produs)
    return produs
```

Observați că:

- `status_code=201` indică explicit că o creare reușită returnează `201 Created`, nu `200 OK`;
- funcția returnează obiectul creat, nu un mesaj de confirmare — aceasta este convenția REST.

### 4.4 Returnarea erorilor cu HTTPException

Când o resursă nu este găsită sau o operație nu poate fi efectuată, se folosește `HTTPException` pentru a returna un cod de stare corespunzător:

```python
# Adăugați acest import la începutul fișierului main.py
from fastapi import FastAPI, HTTPException

# Adăugați acest endpoint în același fișier, alături de cele definite anterior
@app.get("/produse/{produs_id}")
def obtine_produs(produs_id: int):
    for produs in inventar:
        if produs.id == produs_id:
            return produs
    raise HTTPException(status_code=404, detail=f"Produsul cu ID-ul {produs_id} nu a fost găsit.")
```

---

## 5. Exercițiu practic: gestiunea unui inventar

### 5.1 Cerințe

Implementați un serviciu web complet pentru gestionarea stocului unui magazin, folosind o listă Python ca bază de date temporară (in-memory).

**Modelul de date** — clasa `Produs` cu câmpurile: `id` (int), `nume` (str), `pret` (float), `stoc` (int).

**Endpoint-urile cerute:**

| Metodă   | Cale                   | Descriere                           | Cod răspuns   |
| -------- | ---------------------- | ----------------------------------- | ------------- |
| `GET`    | `/produse`             | Returnează lista tuturor produselor | `200`         |
| `GET`    | `/produse/{produs_id}` | Returnează un produs după ID        | `200` / `404` |
| `POST`   | `/produse`             | Adaugă un produs nou în inventar    | `201`         |
| `DELETE` | `/produse/{produs_id}` | Șterge produsul cu ID-ul dat        | `200` / `404` |

### 5.2 Cod de pornire

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Gestiune inventar", version="1.0.0")


class Produs(BaseModel):
    id: int
    nume: str
    pret: float
    stoc: int = 0


inventar: list[Produs] = []


@app.get("/produse")
def obtine_toate_produsele():
    return inventar


@app.get("/produse/{produs_id}")
def obtine_produs(produs_id: int):
    for produs in inventar:
        if produs.id == produs_id:
            return produs
    raise HTTPException(status_code=404, detail=f"Produsul cu ID-ul {produs_id} nu a fost găsit.")


@app.post("/produse", status_code=201)
def adauga_produs(produs: Produs):
    inventar.append(produs)
    return produs


# TODO: Implementați endpoint-ul DELETE /produse/{produs_id}
```

### 5.3 Indicații

- Folosiți `raise HTTPException(status_code=404, ...)` dacă produsul de șters nu există.
- La ștergere reușită, returnați produsul șters sau un mesaj de confirmare — alegeți una dintre variante și justificați alegerea.
- Testați toate endpoint-urile prin Swagger UI (`/docs`) înainte de a considera exercițiul încheiat.

### 5.4 Extindere opțională (bonus)

- Adăugați un endpoint `PUT /produse/{produs_id}` care actualizează complet un produs existent.
- Adăugați un parametru de interogare `stoc_minim` la `GET /produse` care să filtreze produsele cu stoc mai mic decât valoarea dată.

---

## Referințe

- [Documentația oficială FastAPI](https://fastapi.tiangolo.com/)
- [Documentația oficială Pydantic v2](https://docs.pydantic.dev/latest/)
- [RFC 9110 — HTTP Semantics](https://httpwg.org/specs/rfc9110.html) (specificația oficială HTTP)
