# Laborator #05: Publicarea aplicației pe internet

## Obiective

La finalul acestui laborator, studenții vor fi capabili să:

- explice diferența dintre un mediu de dezvoltare și unul de producție;
- gestioneze configurația sensibilă a aplicației prin variabile de mediu și fișiere `.env`;
- servească fișierele frontend direct din FastAPI folosind `StaticFiles`;
- pregătească un proiect Python pentru deployment: `requirements.txt`, structură de fișiere, configurare prin variabile de mediu;
- publice o aplicație FastAPI completă pe Render.com folosind GitHub și `render.yaml`;
- descrie conceptul de containerizare cu Docker și avantajele sale față de deployment tradițional.

---

## 1. De la localhost la internet

Pe parcursul laboratoarelor anterioare, aplicația a rulat exclusiv pe calculatorul propriu, accesibilă la adresa `http://localhost:8000`. Această adresă nu este vizibilă nimănui din afara rețelei locale - oricine altcineva încearcă să o acceseze primește o eroare de conexiune.

**Deployment-ul** este procesul prin care o aplicație este instalată și pornită pe un server accesibil din internet, obținând o adresă publică de forma `https://gestionar-sarcini.onrender.com`.

Diferența între un mediu de **dezvoltare** (*development*) și unul de **producție** (*production*) nu se rezumă la locul unde rulează aplicația:

| Aspect                  | Dezvoltare (local)              | Producție (cloud)                      |
| ----------------------- | ------------------------------- | -------------------------------------- |
| Adresă                  | `http://localhost:8000`         | `https://aplicatie.onrender.com`       |
| Protocol                | HTTP                            | HTTPS (gestionat automat de platformă) |
| Repornire la modificări | `--reload` automat              | Declanșat de un nou `git push`         |
| Date sensibile          | Fișier `.env` local (nu în Git) | Variabile de mediu în dashboard        |
| Baza de date            | Fișier `.db` local, persistent  | Efemeră sau serviciu extern            |

Vom folosi **Render.com** - o platformă cloud cu un nivel gratuit suficient pentru proiecte de învățare. Fluxul de lucru este:

```
Cod local
    │  git push
    ▼
GitHub (depozit public sau privat)
    │  Render detectează modificarea și declanșează build
    ▼
Render.com (server cloud Linux)
    │  pip install -r requirements.txt
    │  uvicorn main:app --host 0.0.0.0 --port $PORT
    ▼
URL public: https://gestionar-sarcini.onrender.com
```

---

## 2. Variabile de mediu

### 2.1 Problema secretelor în cod

În `main.py`, configurația de securitate arată momentan astfel:

```python
SECRET_KEY = "cheie-secreta-foarte-lunga-..."
ALGORITHM = "HS256"
EXPIRARE_TOKEN_MINUTE = 30
```

Dacă acest fișier este urcat pe GitHub - fie pe un depozit public, fie pe unul privat care ar putea fi compromis - oricine poate citi cheia secretă și poate genera tokene JWT valide pentru orice utilizator al aplicației. Aceasta este una dintre cele mai frecvente vulnerabilități de securitate în proiectele de început.

Soluția este separarea **codului** de **configurație**: codul se versionează și se urcă pe GitHub, configurația sensibilă rămâne exclusiv în mediul de rulare.

### 2.2 Fișierul `.env` și biblioteca `python-dotenv`

Un fișier `.env` este un fișier text simplu care conține perechi cheie-valoare:

```
SECRET_KEY=o-cheie-lunga-si-aleatorie-generata-cu-openssl-rand
ALGORITHM=HS256
EXPIRARE_TOKEN_MINUTE=30
```

Biblioteca `python-dotenv` citește automat acest fișier și populează variabilele de mediu ale procesului curent. Instalați-o:

```bash
pip install python-dotenv
```

Actualizați secțiunea de configurare din `main.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()  # Citeste .env daca fisierul exista; nu face nimic altfel

SECRET_KEY = os.environ.get("SECRET_KEY", "cheie-implicita-doar-pentru-dev")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
EXPIRARE_TOKEN_MINUTE = int(os.environ.get("EXPIRARE_TOKEN_MINUTE", "30"))
```

`os.environ.get("CHEIE", "valoare_implicita")` returnează valoarea variabilei de mediu dacă există, sau valoarea implicită altfel. Valoarea implicită permite aplicației să pornească local fără fișier `.env`, dar în producție variabila trebuie setată explicit.

> **Important:** Adăugați `.env` în `.gitignore` **înainte** de primul `git push`. Odată ce un secret a ajuns în istoricul Git, trebuie tratat ca și compromis - chiar dacă ștergeți fișierul ulterior, istoricul Git îl păstrează pentru totdeauna.

> **Notă:** Generați o cheie secretă puternică cu comanda: `python -c "import secrets; print(secrets.token_hex(32))"`. Rezultatul este un șir de 64 de caractere hexadecimale aleatorii - imposibil de ghicit prin forță brută.

### 2.3 Fișierul `.gitignore`

Creați fișierul `.gitignore` în directorul rădăcină al proiectului:

```
# Configuratie locala - nu se urca pe GitHub
.env

# Baza de date locala
*.db

# Cache Python
__pycache__/
*.pyc
*.pyo

# Mediul virtual
venv/
.venv/
```

---

## 3. Servirea frontend-ului din FastAPI

### 3.1 Avantajele servirii din același server

Până acum, `index.html` (Lab #04) și FastAPI rulau pe porturi diferite, necesitând configurare CORS. Dacă FastAPI servește direct fișierele HTML, cele două componente devin parte din același **origin** - browserul nu mai blochează cererile, configurarea CORS devine opțională, iar deployment-ul se simplifică la un singur serviciu.

```
Înainte (două servere separate):
  Browser → http://localhost:5500/index.html  (Live Server)
  Browser → http://localhost:8000/sarcini     (FastAPI) ← CORS necesar

După (un singur server):
  Browser → http://localhost:8000/            (FastAPI serveste index.html)
  Browser → http://localhost:8000/sarcini     (FastAPI API) ← fara CORS
```

### 3.2 Montarea StaticFiles

FastAPI poate servi fișiere statice (HTML, CSS, JS, imagini) prin `StaticFiles`. Creați un director `static/` și mutați `index.html` în el:

```
gestionar-sarcini/
├── main.py
├── requirements.txt
├── .env
├── .gitignore
└── static/
    └── index.html
```

Adăugați importul la **topul** `main.py`, alături de celelalte importuri:

```python
from fastapi.staticfiles import StaticFiles
```

Adăugați montarea la **finalul** `main.py`, **după toate definițiile de endpoint-uri**:

```python
# Trebuie sa fie ULTIMUL apel - prinde toate rutele nerezolvate de endpoint-uri
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

Parametrul `html=True` activează comportamentul SPA: orice URL necunoscut returnează `index.html`.

> **Important:** `app.mount()` trebuie plasat **după** toate decoratorii `@app.get()`, `@app.post()` etc. FastAPI parcurge rutele în ordinea definirii lor - dacă `StaticFiles` este primul, va intercepta toate cererile, inclusiv cele către `/sarcini` sau `/autentificare`, returnând 404.

### 3.3 Actualizarea frontend-ului pentru URL relativ

Acum că frontend-ul și API-ul sunt pe același server, adresa API-ului se simplifică. Modificați constanta `API` din `index.html`:

```javascript
// Inainte (port hardcodat pentru Live Server):
const API = "http://localhost:8000";

// Dupa (URL relativ - functioneaza pe orice domeniu):
const API = "";
```

Cu `API = ""`, un apel de forma `fetch(API + "/sarcini")` devine `fetch("/sarcini")` - o cale relativă față de originea curentă, fie că aceasta este `http://localhost:8000` sau `https://gestionar-sarcini.onrender.com`.

Pentru a testa local cu noua configurație, porniți serverul cu `uvicorn main:app --reload` și accesați `http://localhost:8000` direct - nu mai este nevoie de Live Server.

---

## 4. Pregătirea pentru deployment pe Render.com

### 4.1 Fișierul requirements.txt actualizat

Render.com instalează dependențele din `requirements.txt` la fiecare deployment. Adăugați `python-dotenv`:

```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.7.0
PyJWT>=2.8.0
passlib[bcrypt]>=1.7.4
python-dotenv>=1.0.0
```

### 4.2 Fișierul render.yaml

Render.com poate fi configurat fie prin interfața web (dashboard), fie printr-un fișier `render.yaml` adăugat în rădăcina proiectului. Acesta este o formă de **Infrastructure as Code** - configurația infrastructurii trăiește alături de cod și se versionează împreună cu acesta.

```yaml
services:
  - type: web
    name: gestionar-sarcini
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SECRET_KEY
        generateValue: true
      - key: ALGORITHM
        value: HS256
      - key: EXPIRARE_TOKEN_MINUTE
        value: 30
      - key: DATABASE_PATH
        value: /tmp/sarcini.db
```

Câteva explicații:

- `generateValue: true` - Render generează automat o valoare aleatorie pentru `SECRET_KEY` la primul deployment, fără a fi necesară specificarea manuală.
- `$PORT` - variabilă de mediu setată automat de Render cu portul pe care trebuie să asculte serverul. Nu hardcodați portul.
- `/tmp/sarcini.db` - directorul `/tmp` este scribil pe serverele Render. Baza de date va fi totuși ștearsă la fiecare deployment nou (a se vedea nota de mai jos).

### 4.3 Pașii de publicare pe Render.com

1. Creați un cont gratuit pe [render.com](https://render.com) (autentificare cu GitHub recomandată).
2. Creați un depozit nou pe GitHub (github.com → **New repository**), copiați URL-ul.
3. Urcați proiectul pe GitHub:
   
   ```bash
   git init
   git add .
   git commit -m "initial commit"
   git remote add origin https://github.com/<username>/<repo>.git
   git branch -M main
   git push -u origin main
   ```
4. În dashboard-ul Render, apăsați **New → Blueprint**.
5. Conectați contul GitHub și selectați depozitul corespunzător.
6. Render detectează `render.yaml` și afișează serviciile care vor fi create.
7. Apăsați **Apply** pentru a porni deployment-ul.
8. Urmăriți log-urile de build în timp real - erorile sunt afișate direct.
9. La finalul build-ului (2-3 minute), Render afișează URL-ul public.

> **Notă:** Fluxul **Blueprint** (pașii de mai sus) este cel care utilizează `render.yaml` automat. Dacă preferați configurarea manuală fără `render.yaml`, folosiți **New → Web Service** și completați câmpurile din interfață - Build Command, Start Command și variabilele de mediu - manual.

> **Notă:** Nivelul gratuit Render pune serviciul în "somn" după 15 minute de inactivitate. Prima cerere după o perioadă de inactivitate durează 30-50 de secunde (pornire la rece - *cold start*). Aceasta este o limitare acceptabilă pentru proiecte de testare și demonstrații.

> **Important:** Fișierul SQLite nu persistă între deployment-uri pe nivelul gratuit Render - sistemul de fișiere este efemer, iar la fiecare nou deployment baza de date este recreată goală. Aceasta este o limitare structurală a SQLite în cloud: pentru date persistente în producție se folosesc baze de date externe (PostgreSQL, MySQL) sau un **Persistent Disk** (opțiune plătită pe Render.com). Pentru scopul acestui laborator, limitarea este acceptabilă.

---

## 5. Proiectul complet pregătit pentru deployment

Structura finală a proiectului:

```
gestionar-sarcini/
├── main.py             ← configuratie prin env vars + StaticFiles la final
├── requirements.txt    ← toate dependentele inclusiv python-dotenv
├── render.yaml         ← configuratia Render
├── .env                ← NU se urca pe GitHub (in .gitignore)
├── .gitignore
└── static/
    └── index.html      ← frontend cu const API = ""
```

Secțiunea de configurare din `main.py` - singura parte care se modifică față de Lab #03:

```python
import os
from dotenv import load_dotenv

# --- restul importurilor din Lab #03 ---

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "cheie-dev-de-inlocuit")
ALGORITHM = os.environ.get("ALGORITHM", "HS256")
EXPIRARE_TOKEN_MINUTE = int(os.environ.get("EXPIRARE_TOKEN_MINUTE", "30"))
DATABASE_PATH = os.environ.get("DATABASE_PATH", "sarcini.db")
```

Referința la baza de date - înlocuiți calea hardcodată cu variabila:

```python
conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
```

Ultimul rând din `main.py`:

```python
# -------- Ultimul rand - dupa toate endpoint-urile --------
app.mount("/", StaticFiles(directory="static", html=True), name="static")
```

### 5.1 Testarea locală înainte de deployment

Verificați că totul funcționează cu noua configurație înainte de `git push`:

1. Creați fișierul `.env` cu `SECRET_KEY=o-valoare-locala`.
2. Porniți serverul: `uvicorn main:app --reload`.
3. Deschideți `http://localhost:8000` - ar trebui să vedeți interfața aplicației.
4. Testați înregistrarea, autentificarea și operațiile CRUD complet.
5. Verificați că nu există erori în consola browser-ului (F12).

### 5.2 Actualizarea după primul deployment

Orice modificare ulterioară se publică automat:

```bash
git add .
git commit -m "descriere modificare"
git push
```

Render detectează push-ul și declanșează automat un nou build și deployment.

---

## 6. Docker - o alternativă pentru deployment

> **Notă:** Această secțiune este teoretică - nu include exercițiu practic. Scopul este familiarizarea cu Docker, standardul industrial pentru deployment și distribuirea aplicațiilor. Testarea codului Python cu `pytest` va fi subiectul laboratorului următor.

### 6.1 Ce este un container Docker

**Docker** este o platformă de **containerizare** care ambalează o aplicație împreună cu toate dependențele ei (interpretor Python, biblioteci, configurație de sistem) într-o unitate portabilă numită **container**.

Diferența față de o mașină virtuală (VM) - conceptul studiat în Laboratorul #01:

| Aspect            | Mașină virtuală (VM)                        | Container Docker                          |
| ----------------- | ------------------------------------------- | ----------------------------------------- |
| Conține           | Sistem de operare complet + aplicație       | Numai aplicația + dependențele necesare   |
| Dimensiune tipică | Gigabytes (GB)                              | Megabytes (MB)                            |
| Timp de pornire   | Minute                                      | Secunde                                   |
| Izolare           | Completă (prin hypervisor)                  | Parțială (kernel Linux partajat cu gazda) |
| Portabilitate     | Mai complexă (imagini de GB, transfer lent) | "Rulează oriunde există Docker"           |

Un container Docker este similar unui fișier executabil autoconținut: copiezi imaginea pe orice server cu Docker instalat și aplicația pornește identic, indiferent de sistemul de operare al gazdei sau de alte aplicații instalate.

### 6.2 Dockerfile

Un **Dockerfile** este un fișier text cu instrucțiuni pentru construirea unei **imagini Docker** - șablonul imuabil din care se pornesc containere. Fiecare instrucțiune creează un **strat** (*layer*) care este memorat în cache: dacă schimbați doar codul aplicației fără să modificați `requirements.txt`, Docker nu va reinstala dependențele la rebuild.

```dockerfile
# Imaginea de baza - Python 3.12 minimal (varianta "slim" reduce dimensiunea)
FROM python:3.12-slim

# Directorul de lucru in interiorul containerului
WORKDIR /app

# Copiem mai intai requirements.txt (separat de cod)
# Astfel, stratul cu pip install ramane in cache daca doar codul se schimba
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiem restul codului aplicatiei
# Nota: creati un fisier .dockerignore care sa excluda .env, *.db, venv/
COPY . .

# Documentare: portul pe care asculta aplicatia (nu deschide portul efectiv)
EXPOSE 8000

# Comanda executata la pornirea containerului
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Înainte de a construi imaginea, creați un fișier `.dockerignore` (similar cu `.gitignore`) pentru a împiedica copierea secretelor și a fișierelor inutile în imagine:

```
.env
*.db
venv/
.venv/
__pycache__/
```

Comenzi esențiale Docker:

```bash
# Construieste imaginea cu eticheta "gestionar-sarcini"
docker build -t gestionar-sarcini .

# Porneste un container; -p mapeaza portul 8000 al containerului la 8000 al gazdei
# --env-file incarca variabilele din .env (fara sa le copieze in imagine)
docker run -p 8000:8000 --env-file .env gestionar-sarcini

# Listeaza containerele care ruleaza
docker ps

# Afiseaza log-urile unui container (dupa ID sau nume)
docker logs <container_id>

# Opreste un container
docker stop <container_id>

# Sterge containerul oprit, apoi imaginea (ordinea conteaza)
docker rm <container_id>
docker rmi gestionar-sarcini
```

### 6.3 Docker Compose

**Docker Compose** este un instrument pentru definirea și pornirea mai multor containere simultan, descrise într-un singur fișier `docker-compose.yml`. Este esențial când aplicația depinde de mai multe servicii - de exemplu: API + bază de date PostgreSQL + server de cache Redis.

Pentru aplicația noastră curentă (cu SQLite), `docker-compose.yml` arată simplu:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"       # port_gazda:port_container
    env_file:
      - .env
    volumes:
      - ./sarcini.db:/app/sarcini.db  # Monteaza fisierul db din gazda in container
```

Directiva `volumes` rezolvă problema persistenței: fișierul `sarcini.db` există pe calculatorul gazdă și este "montat" în container. Chiar dacă containerul este șters și recreat, datele rămân.

> **Important:** Dacă `sarcini.db` nu există pe gazdă în momentul `docker compose up`, Docker îl va crea ca **director** (nu fișier), ceea ce va face ca SQLite să eșueze. Creați fișierul gol înainte de prima pornire: `touch sarcini.db` (Linux/macOS) sau `New-Item sarcini.db` (PowerShell).

Comenzi Docker Compose:

```bash
# Porneste toate serviciile (in background cu -d / --detach)
docker compose up -d

# Afiseaza log-urile in timp real
docker compose logs -f

# Opreste containerele (fara sa le stearga)
docker compose stop

# Opreste si sterge containerele (volumele raman)
docker compose down

# Rebuild si repornire dupa modificari in cod
docker compose up -d --build
```

### 6.4 Docker networks

Când mai multe containere rulează împreună prin Docker Compose, Docker creează automat o **rețea virtuală internă** izolată. Containerele comunică între ele folosind **numele serviciului** ca hostname, nu adresa `localhost`.

Exemplu: o variantă viitoare a aplicației care migrează de la SQLite la PostgreSQL:

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:parola@baza-de-date:5432/sarcini
    depends_on:
      - baza-de-date

  baza-de-date:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=parola
      - POSTGRES_DB=sarcini
    volumes:
      - date-postgres:/var/lib/postgresql/data

volumes:
  date-postgres:    # Volum gestionat de Docker - persista intre restartari
```

> **Notă:** `depends_on` garantează doar că **containerul** `baza-de-date` a pornit, nu că PostgreSQL din interior acceptă conexiuni. Dacă `api` pornește prea rapid, va obține o eroare de conexiune. În producție, se adaugă un `healthcheck` și `condition: service_healthy` la `depends_on` - un subiect acoperit în documentația Docker Compose.

```
┌─────────────────────────────────────────────────┐
│              Rețea Docker (izolată)             │
│                                                 │
│  ┌──────────────┐       ┌───────────────────┐   │
│  │     api      │──────▶│   baza-de-date    │   │
│  │  port 8000   │       │   port 5432       │   │
│  └──────────────┘       └───────────────────┘   │
│          │                                      │
└──────────│──────────────────────────────────────┘
           │  port 8000 expus calculatorului gazda
           ▼
     Browser (localhost:8000)
```

Containerul `api` se conectează la PostgreSQL folosind hostname-ul `baza-de-date` (numele serviciului din `docker-compose.yml`). Portul `5432` al bazei de date nu este expus în afara rețelei Docker - este accesibil exclusiv containerului `api`.

### 6.5 Docker și platformele cloud

**Render.com** (și platformele similare: Railway, Fly.io, Heroku) rulează intern aplicațiile în containere. Fișierul `render.yaml` este o abstracție de nivel înalt: când nu există un `Dockerfile`, Render folosește propriul sistem de build (**Nixpacks**) care detectează automat limbajul și construiește mediul de execuție. Dacă adăugați un `Dockerfile` în proiect, Render îl va folosi în locul Nixpacks.

Odată ce înțelegeți Docker, puteți deployal orice aplicație pe orice platformă cloud care acceptă containere - aceasta include practic toți marii furnizori (AWS, Google Cloud, Azure, DigitalOcean). Containerele reprezintă standardul industrial pentru distribuirea și rularea aplicațiilor în medii de producție.

---

## 7. Exercițiu practic: deployment-ul gestionarului de sarcini

### Cerințe

**A. Deployment complet pe Render.com**

Publicați aplicația completă (backend + frontend) pe Render.com:

1. Creați fișierele `.env`, `.gitignore`, `render.yaml` și `requirements.txt` conform secțiunilor 2-4.
2. Mutați `index.html` în `static/` și modificați `const API = ""`.
3. Adăugați `app.mount(...)` ca ultim rând din `main.py`.
4. Urcați proiectul pe GitHub și conectați depozitul la Render.
5. Verificați că aplicația funcționează la URL-ul public generat.

**B. Variabila `DATABASE_PATH`**

Faceți calea bazei de date configurabilă:

```python
DATABASE_PATH = os.environ.get("DATABASE_PATH", "sarcini.db")
```

Înlocuiți toate referințele la `"sarcini.db"` (sau cum ați denumit fișierul) cu variabila `DATABASE_PATH`. Adăugați-o în `.env` local cu valoarea `sarcini.db` și în `render.yaml` cu valoarea `/tmp/sarcini.db`.

### Tabelul fișierelor după implementare

| Fișier              | Urcat pe GitHub? | Observații                                         |
| ------------------- | ---------------- | -------------------------------------------------- |
| `main.py`           | Da               | Configurație prin `os.environ.get()`               |
| `requirements.txt`  | Da               | Include `python-dotenv`                            |
| `render.yaml`       | Da               | Fără `SECRET_KEY` explicit - `generateValue: true` |
| `.gitignore`        | Da               | Listează `.env` și `*.db`                          |
| `.env`              | **Nu**           | Conține `SECRET_KEY` real - rămâne local           |
| `static/index.html` | Da               | `const API = ""`                                   |

### Indicații

- Dacă Render afișează erori la build, verificați tab-ul **Logs** din dashboard. Cel mai frecvent: `requirements.txt` incomplet sau erori de sintaxă Python.
- Dacă aplicația pornește dar toate cererile API returnează 404, verificați că `app.mount(...)` este **ultimul** rând din `main.py`.
- Dacă cererile protejate returnează `500 Internal Server Error`, verificați că variabila `SECRET_KEY` apare în tab-ul **Environment** din dashboard-ul Render.
- Primul acces după o perioadă de inactivitate durează 30-50 de secunde (*cold start*) - aceasta este normal pe nivelul gratuit.
- Datele înregistrate se pierd la fiecare deployment. Creați un cont de test dedicat acestui laborator.

### Extindere opțională (bonus)

- Adăugați un endpoint `GET /healthz` care returnează `{"status": "ok"}` fără a necesita autentificare. Render poate monitoriza automat acest endpoint pentru a verifica că aplicația a pornit corect (*health check*) - configurați-l în `render.yaml` cu `healthCheckPath: /healthz`.
- Instalați **Docker Desktop** și rulați aplicația local într-un container folosind `Dockerfile`-ul din secțiunea 6.2 - verificați că funcționează identic cu varianta fără Docker.

---

## Referințe

- [Documentația Render.com](https://render.com/docs)
- [Render - Infrastructure as Code (render.yaml)](https://render.com/docs/infrastructure-as-code)
- [FastAPI - Fișiere statice (StaticFiles)](https://fastapi.tiangolo.com/tutorial/static-files/)
- [python-dotenv - documentație](https://pypi.org/project/python-dotenv/)
- [Documentația Docker - Get started](https://docs.docker.com/get-started/)
- [Documentația Docker Compose](https://docs.docker.com/compose/)
- [Docker Hub - imagini oficiale Python](https://hub.docker.com/_/python)
