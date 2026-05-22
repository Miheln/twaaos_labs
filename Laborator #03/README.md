# Laborator #03 - Agenda de sarcini

API FastAPI pentru sarcini personale, cu baza de date SQLite si autentificare JWT.

Baza de date se creeaza automat in fisierul `sarcini.db`.

## Pornire

```bash
./start.sh
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Test rapid in Swagger

1. Creeaza cont cu `POST /inregistrare`.
2. Apasa `Authorize`.
3. La `username` pui emailul, iar la `password` pui parola.
4. Testeaza endpoint-urile pentru `/sarcini`.

Oprire server: `Ctrl+C`.
