# Laborator 07 - Versiune finala

Aplicatia este versiunea imbunatatita pentru final: Homemade To Do + pagina About me.

Frontend-ul este in `static/index.html` si este servit direct de FastAPI. Nu mai este nevoie de server separat pe portul 5500.

## Pornire locala

```bash
./start.sh
```

Deschide:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## Render

Pentru Render se poate folosi acelasi serviciu ca la Lab 5. Schimbarea minima este root-ul:

```text
Laborator 07
```

Variabile importante:

- `SECRET_KEY` - generata automat de Render
- `ALGORITHM` - `HS256`
- `EXPIRARE_TOKEN_MINUTE` - `30`
- `DATABASE_PATH` - `/tmp/sarcini.db`

Pe Render, baza SQLite din `/tmp` se poate pierde la redeploy. Pentru laborator este acceptabil.
