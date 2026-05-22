# Laborator #04 - Panou de sarcini

Aplicatie cu API FastAPI si interfata web in HTML, Bootstrap si JavaScript.

API-ul foloseste SQLite si JWT. Pagina web foloseste `fetch()` si pastreaza tokenul in `localStorage`.

## Pornire

```bash
./start.sh
```

Se pornesc doua servicii:

- API: `http://127.0.0.1:8000/docs`
- Interfata: `http://127.0.0.1:5500/index.html`

## Test rapid

1. Creeaza cont in pagina web.
2. Intra cu email si parola.
3. Adauga o sarcina.
4. Editeaza, finalizeaza sau sterge sarcina.
5. Bifeaza filtrul pentru sarcini nefinalizate.

Oprire: `Ctrl+C`.
