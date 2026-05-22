# Laborator #02 - Catalog produse

Serviciu web simplu pentru produse, construit cu FastAPI.

Datele sunt tinute in memoria programului. Daca serverul este oprit, lista se goleste.

## Pornire

```bash
./start.sh
```

Dupa pornire, se deschide documentatia Swagger:

```text
http://127.0.0.1:8000/docs
```

## Endpoint-uri principale

- `GET /produse` - afiseaza produsele
- `GET /produse/{produs_id}` - afiseaza un produs dupa ID
- `POST /produse` - adauga un produs
- `PUT /produse/{produs_id}` - modifica un produs
- `DELETE /produse/{produs_id}` - sterge un produs

Oprire server: `Ctrl+C`.
