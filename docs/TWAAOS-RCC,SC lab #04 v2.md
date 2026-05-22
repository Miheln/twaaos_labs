# Laborator #04: Interfață web pentru gestionarul de sarcini

## Obiective

La finalul acestui laborator, studenții vor fi capabili să:

- explice rolul unui client web și diferența dintre Swagger UI și o interfață proprie;
- descrie politica Same-Origin și mecanismul CORS din perspectiva _frontend_;
- construiască un layout responsive folosind componente Bootstrap incluse via CDN;
- utilizeze `fetch()` pentru cereri HTTP cu antete și corp JSON din browser;
- gestioneze starea de autentificare într-o aplicație de o singură pagină folosind `localStorage`;
- integreze o interfață web completă cu un serviciu REST existent, acoperind fluxurile de înregistrare, autentificare și CRUD.

---

## 1. De la API la interfață vizuală

În laboratoarele anterioare ați construit un serviciu web complet - cu endpoint-uri, bază de date și autentificare JWT. Tot testarea s-a făcut prin **Swagger UI**, interfața automată generată de FastAPI. Swagger UI este un instrument de testare, nu o aplicație pentru utilizatori finali. Acum vom construi o **interfață proprie** pe care orice utilizator o poate folosi fără să știe ce este un HTTP request.

| Caracteristică | Swagger UI | Interfața proprie |
|---|---|---|
| Scop | Testare și documentare API | Utilizare de către orice persoană |
| Cine o construiește | FastAPI automat | Dezvoltatorul frontend |
| Cunoștințe necesare | HTTP, JSON, Bearer token | Nimic tehnic |
| Personalizare vizuală | Minimă | Completă |

Aplicația pe care o vom construi este o **aplicație de o singură pagină** (*single-page application* - SPA) - un singur fișier HTML care nu se reîncarcă niciodată complet. Schimbările vizuale se fac prin afișarea și ascunderea unor secțiuni din pagină cu ajutorul JavaScript.

Fluxul de date arată astfel:

```
index.html (în browser)
    │
    │  fetch("http://localhost:8000/sarcini", { headers: { Authorization: ... } })
    ▼
FastAPI (localhost:8000)
    │
    │  [{ "id": 1, "titlu": "Cumpărături", ... }, ...]
    ▼
JavaScript actualizează DOM-ul paginii
```

Stack-ul ales urmărește simplitatea: **Bootstrap** via CDN pentru aspect vizual (fără să scriem CSS manual), **JavaScript** fără framework-uri (rulează direct în browser, fără instalare) și **`fetch()`** integrat în orice browser modern. Nu este nevoie de npm, node_modules sau comenzi de build - se deschide fișierul HTML și aplicația funcționează.

---

## 2. CORS

Până acum ați configurat `CORSMiddleware` în FastAPI fără să vedeți efectele în practică, deoarece Swagger UI rulează pe același server. Când componenta _frontend_ corespunde unui fișier HTML deschis din altă locație, **CORS devine foarte important**.

**) CORS - cross-origin resource sharing*

### 2.1 Politica _Same-Origin_

Browserul aplică politica **Same-Origin** (*Same-Origin Policy*): un script dintr-o pagină poate face cereri HTTP doar către aceeași **origine** - adică același protocol, același host și același port. Originea nu este definită de server, ci impusă de browser ca măsură de securitate.

Exemplu: dacă fișierul HTML este servit de la `http://localhost:5500`, iar API-ul rulează pe `http://localhost:8000`, originile sunt **diferite** (porturile diferă). Browserul va bloca orice cerere cross-origin dacă serverul nu o permite explicit.

### 2.2 Preflight și headerele non-simple

Când JavaScript trimite o cerere cu headerul `Authorization: Bearer ...`, browserul trimite automat o cerere preliminară de tip **preflight** - o cerere `OPTIONS` care întreabă serverul dacă permite această operație.

```
→ OPTIONS /sarcini HTTP/1.1
  Origin: http://localhost:5500
  Access-Control-Request-Method: GET
  Access-Control-Request-Headers: authorization

← HTTP/1.1 200 OK
  Access-Control-Allow-Origin: http://localhost:5500
  Access-Control-Allow-Headers: authorization
  Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE

→ GET /sarcini HTTP/1.1
  Authorization: Bearer eyJhbGci...
```

Abia după ce preflight-ul reușește, browserul trimite cererea reală.

### 2.3 Configurarea CORSMiddleware pentru frontend

Actualizați configurarea CORS din `main.py` pentru a permite originea de la care va fi servit fișierul HTML:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",  # VS Code Live Server (portul implicit)
        "http://127.0.0.1:5500",  # Varianta alternativa a aceluiasi server
        "null",                   # Fisier deschis direct din sistem de fisiere
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

> ⚠️ **Important:** `allow_origins=["*"]` nu funcționează împreună cu `allow_credentials=True`. Listați explicit originile permise sau folosiți `"null"` pentru fișiere deschise local. În producție, înlocuiți aceste valori cu domeniul real al componentei frontend.

> **Notă:** Extensia **Live Server** din VS Code servește fișierul HTML pe `http://localhost:5500` și reîncarcă automat pagina la orice modificare. Este metoda recomandată pentru dezvoltare - click dreapta pe `index.html` → *Open with Live Server*. Alternativ, fișierul poate fi deschis direct în browser (dublu-click), caz în care originea este `null`.

---

## 3. Structura unui fișier HTML

Un fișier HTML este un document text structurat în etichete (*tag-uri*). Fiecare element are o etichetă de deschidere și una de închidere: `<div>conținut</div>`. Atributele modifică comportamentul sau aspectul elementului: `<button class="btn" id="btn-login">`.

### 3.1 Anatomia unui fișier HTML cu Bootstrap

```html
<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Aplicația mea</title>
    <!-- Bootstrap CSS - stilurile vizuale -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

    <!-- Conținutul vizibil al paginii -->
    <div class="container mt-4">
        <div class="row">
            <div class="col-md-6">
                <p>Coloana stânga</p>
            </div>
            <div class="col-md-6">
                <p>Coloana dreapta</p>
            </div>
        </div>
    </div>

    <!-- Bootstrap JS - componente interactive (meniuri, modals etc.) -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
    <!-- Scriptul propriu - întotdeauna după Bootstrap JS -->
    <script>
        // Codul JavaScript propriu
    </script>
</body>
</html>
```

`<head>` conține metadate și resurse externe - nu afișează nimic vizibil. `<body>` conține tot ce vede utilizatorul. Bootstrap CSS se include în `<head>`, iar scripturile JavaScript se includ la sfârșitul `<body>`, după tot conținutul, pentru ca elementele paginii să existe deja când scriptul rulează.

### 3.2 Sistemul de grid Bootstrap

Bootstrap împarte fiecare rând în **12 coloane**. Clasa `col-md-6` înseamnă "ocupă 6 coloane pe ecrane medii și mari" - adică jumătate din lățime. Pe ecrane mici (telefon), coloanele se stivuiesc automat pe verticală.

### 3.3 Clase Bootstrap esențiale pentru această aplicație

| Clasă | Efect |
|---|---|
| `d-none` | Ascunde elementul (echivalent `display: none`) |
| `d-block` | Afișează elementul |
| `btn btn-primary` | Buton albastru |
| `btn btn-outline-danger` | Buton cu contur roșu |
| `btn btn-sm` | Buton mic |
| `alert alert-danger` | Casetă roșie pentru erori |
| `alert alert-success` | Casetă verde pentru mesaje de succes |
| `badge bg-success` | Etichetă verde (ex: "Finalizată") |
| `badge bg-secondary` | Etichetă gri (ex: "În progres") |
| `card` / `card-body` | Container cu umbră și bordură |
| `form-control` | Stil pentru câmpuri `<input>` și `<textarea>` |
| `form-label` | Stil pentru eticheta unui câmp |
| `w-100` | Lățime 100% |

Clasele `d-none` și `d-block` sunt deosebit de importante - prin adăugarea și eliminarea lor din JavaScript vom comuta între ecranul de autentificare și cel de sarcini, fără reîncărcarea paginii.

### 3.4 Atributul `id` ca punte spre JavaScript

Orice element HTML poate primi un atribut `id` unic în pagină. Acesta este modul prin care JavaScript găsește și modifică elementele:

```html
<div id="mesaj-eroare" class="alert alert-danger d-none">Eroare!</div>
```

Din JavaScript: `document.getElementById("mesaj-eroare")` - returnează elementul de mai sus.

> **Notă:** [LayoutIt!](https://www.layoutit.com/) este un instrument vizual care generează HTML cu grid Bootstrap prin drag-and-drop, fără a scrie cod manual. Este util pentru a prototipa rapid structura unei pagini înainte de a adăuga logica JavaScript.

---

## 4. JavaScript în browser

JavaScript este limbajul care animează paginile web - permite modificarea conținutului, reacția la acțiunile utilizatorului și comunicarea cu serverul. Spre deosebire de Python, JavaScript rulează **în browser**, nu pe server.

### 4.1 Selectarea și modificarea elementelor

```javascript
// Obține referința la un element după id
const titlu = document.getElementById("titlu-pagina");

// Modifică textul elementului
titlu.textContent = "Bun venit!";

// Modifică conținutul HTML (permite inserarea de tag-uri)
titlu.innerHTML = "<strong>Bun venit!</strong>";
```

### 4.2 Afișarea și ascunderea elementelor

```javascript
const panel = document.getElementById("panel-sarcini");

// Ascunde elementul
panel.classList.add("d-none");

// Afișează elementul
panel.classList.remove("d-none");

// Comută între ascuns și vizibil
panel.classList.toggle("d-none");
```

### 4.3 Reacția la acțiunile utilizatorului

```javascript
const buton = document.getElementById("btn-login");

buton.addEventListener("click", function() {
    console.log("Butonul a fost apăsat!");
    // Codul care se execută la click
});

// Forma prescurtată cu arrow function (echivalentă)
buton.addEventListener("click", () => {
    console.log("Butonul a fost apăsat!");
});
```

Alternativ, direct în HTML: `<button onclick="numefunctie()">`. Această formă este folosită în aplicația din acest laborator pentru simplitate.

### 4.4 Variabile și tipuri

```javascript
const API = "http://localhost:8000"; // Constanta - nu poate fi reatribuita
let token = null;                    // Variabila - poate fi modificata

// Template literal - interpolare de variabile
const url = `${API}/sarcini/${id}`;  // echivalent: API + "/sarcini/" + id
```

Folosiți `const` pentru valori care nu se schimbă și `let` pentru cele care se modifică. Evitați `var` - are un comportament diferit față de `let` și poate produce erori greu de depanat.

### 4.5 Funcții async și await

Comunicarea cu serverul durează - browserul nu trebuie să "înghețe" în așteptare. Funcțiile declarate `async` pot folosi `await` pentru a "pausa" execuția până sosește răspunsul, fără a bloca interfața.

```javascript
// Fara async/await - greu de citit
fetch(url).then(function(raspuns) {
    return raspuns.json();
}).then(function(date) {
    console.log(date);
});

// Cu async/await - echivalent, mult mai lizibil
async function incarcaDate() {
    const raspuns = await fetch(url);
    const date = await raspuns.json();
    console.log(date);
}
```

Orice funcție care folosește `await` trebuie declarată `async`. Acesta este un pattern pe care îl veți folosi pentru toate cererile HTTP din această aplicație.

> **Notă:** `async/await` este un mod simplificat de a lucra cu **Promises** - mecanismul intern al JavaScript pentru operații asincrone. Nu este nevoie să înțelegeți Promises în profunzime pentru acest laborator.

### 4.6 Stocarea persistentă cu localStorage

`localStorage` este un depozit de tip cheie-valoare din browser. Datele persistă chiar și după închiderea tab-ului sau reîncărcarea paginii.

```javascript
// Salvare
localStorage.setItem("token", "eyJhbGci...");

// Citire (returneaza null daca nu exista)
const token = localStorage.getItem("token");

// Stergere
localStorage.removeItem("token");
```

> ⚠️ **Important:** Orice script JavaScript din pagină poate citi `localStorage`. Nu stocați date sensibile dincolo de ce este strict necesar. Tokenul JWT este acceptabil - el oricum expiră și serverul îl revalidează la fiecare cerere. Totuși, evitați să stocați parole sau date personale suplimentare.

---

## 5. Cereri HTTP cu fetch()

`fetch()` este funcția built-in a browserului pentru cereri HTTP - echivalentul clientului HTTP din Swagger UI, dar controlabil din cod.

### 5.1 Structura unui apel fetch

```javascript
async function exempluGet() {
    const token = localStorage.getItem("token");

    const raspuns = await fetch("http://localhost:8000/sarcini", {
        method: "GET",                                  // Metoda HTTP
        headers: {
            "Authorization": `Bearer ${token}`         // Token JWT in header
        }
    });

    if (!raspuns.ok) {
        console.error("Eroare:", raspuns.status);
        return;
    }

    const sarcini = await raspuns.json();              // Decodare JSON
    console.log(sarcini);
}
```

Observați că sunt necesare **două** `await`: primul pentru trimiterea cererii și primirea headerelor de răspuns, al doilea pentru citirea și decodarea corpului răspunsului.

| Opțiune | Scop |
|---|---|
| `method` | Metoda HTTP: `"GET"`, `"POST"`, `"PUT"`, `"PATCH"`, `"DELETE"` |
| `headers` | Obect cu headerele cererii (Authorization, Content-Type etc.) |
| `body` | Corpul cererii - obligatoriu pentru POST/PUT, absent pentru GET/DELETE |
| `response.ok` | `true` dacă status-ul este între 200-299 |
| `response.status` | Codul numeric al status-ului (200, 401, 404 etc.) |

### 5.2 Cerere POST cu corp JSON

```javascript
async function adaugaSarcina(titlu, descriere) {
    const token = localStorage.getItem("token");

    const raspuns = await fetch("http://localhost:8000/sarcini", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",        // Obligatoriu pentru JSON
            "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ titlu: titlu, descriere: descriere })
    });

    if (raspuns.ok) {
        const sarcinaNoua = await raspuns.json();
        console.log("Sarcina creată:", sarcinaNoua);
    }
}
```

### 5.3 Cerere DELETE

```javascript
async function stergeSarcina(id) {
    const token = localStorage.getItem("token");

    const raspuns = await fetch(`http://localhost:8000/sarcini/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` }
        // DELETE nu are corp
    });

    if (raspuns.ok) {
        console.log("Sarcina ștearsă.");
    }
}
```

### 5.4 Cazul special: autentificarea

> ⚠️ **Important:** Endpoint-ul `POST /autentificare` din FastAPI folosește `OAuth2PasswordRequestForm`, care impune formatul `application/x-www-form-urlencoded` - **nu** JSON. Aceasta este o diferență față de toate celelalte endpoint-uri și este o sursă frecventă de confuzie.

Dacă trimiteți JSON la `/autentificare`, serverul va răspunde cu `422 Unprocessable Entity`. Soluția este `URLSearchParams`:

```javascript
async function autentifica(email, parola) {
    // URLSearchParams genereaza formatul "username=...&password=..."
    const dateFormular = new URLSearchParams();
    dateFormular.append("username", email);  // campul se numeste "username", nu "email"
    dateFormular.append("password", parola);

    const raspuns = await fetch("http://localhost:8000/autentificare", {
        method: "POST",
        body: dateFormular
        // Nu specificati Content-Type - URLSearchParams il seteaza automat corect
    });

    if (raspuns.ok) {
        const date = await raspuns.json();
        console.log(date.access_token);     // Tokenul JWT
    }
}
```

Câmpul se numește `username` (nu `email`) deoarece `OAuth2PasswordRequestForm` este un standard FastAPI care folosește această denumire, indiferent de ce stochează aplicația.

> **Notă:** DevTools-ul browserului (tasta `F12`, tab-ul **Network**) afișează toate cererile HTTP trimise de pagină - exact ca Swagger UI, dar pentru propriul cod. Puteți inspecta headerele, corpul cererii și răspunsul complet al serverului. Este instrumentul principal de depanare pentru componenta frontend.

---

## 6. Gestionarea stării de autentificare

O aplicație web are întotdeauna o **stare** - un set de informații care determină ce vede utilizatorul la un moment dat. Aplicația noastră are două stări principale:

```
[Neautentificat] ──── login reușit ────► [Autentificat]
                                              │
      ◄──────────── logout ──────────────────┘
```

Starea este determinată de prezența sau absența tokenului în `localStorage`. La fiecare modificare de stare (login, logout) se apelează o singură funcție - `actualizeazaUI()` - care verifică tokenul și afișează secțiunea corespunzătoare.

### 6.1 Funcțiile de gestionare a tokenului

```javascript
function salveazaToken(token) {
    localStorage.setItem("token", token);
}

function obtineToken() {
    return localStorage.getItem("token"); // null daca nu exista
}

function deconecteaza() {
    localStorage.removeItem("token");
    actualizeazaUI(); // actualizeaza interfata imediat
}
```

### 6.2 Afișarea email-ului din token

Tokenul JWT conține în payload email-ul utilizatorului (câmpul `sub`). Îl putem extrage client-side fără o cerere suplimentară la server, decodând a doua parte a tokenului din Base64:

```javascript
const token = obtineToken();
const payload = JSON.parse(atob(token.split(".")[1]));
console.log(payload.sub); // ex: "utilizator@example.com"
```

> **Notă:** Această decodare servește exclusiv afișării în interfață. Browserul nu verifică semnătura tokenului - asta face serverul la fiecare cerere protejată. Un utilizator care modifică manual tokenul în localStorage va vedea date greșite în interfață, dar cererile sale vor fi respinse cu `401 Unauthorized` de server.

---

## 7. Aplicația completă

Aplicația are două stări vizuale principale. În starea neautentificată se afișează un card cu formularul de înregistrare sau autentificare (comutabile printr-un link). În starea autentificată se ascunde cardul de autentificare și se afișează secțiunea de sarcini - un formular de adăugare urmat de lista sarcinilor utilizatorului curent. Navbar-ul afișează permanent titlul aplicației; în starea autentificată apar în plus email-ul utilizatorului și butonul de deconectare.

Toate funcțiile JavaScript sunt grupate în blocul `<script>` de la finalul fișierului. Constanta `API` este definită o singură dată la top - dacă portul serverului se schimbă, modificarea se face într-un singur loc.

```html
<!DOCTYPE html>
<html lang="ro">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestionar de sarcini</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>

<nav class="navbar navbar-dark bg-primary">
    <div class="container">
        <span class="navbar-brand fw-bold">Gestionar de sarcini</span>
        <div id="info-utilizator" class="d-none align-items-center gap-3">
            <span id="email-utilizator" class="text-white small"></span>
            <button class="btn btn-outline-light btn-sm" onclick="deconecteaza()">Deconectare</button>
        </div>
    </div>
</nav>

<div class="container mt-4">

    <!-- -------- Sectiunea de autentificare -------- -->
    <div id="sectiune-auth">
        <div class="row justify-content-center">
            <div class="col-md-5">

                <!-- Formularul de inregistrare -->
                <div id="form-inregistrare" class="card">
                    <div class="card-body">
                        <h5 class="card-title">Înregistrare</h5>
                        <div id="eroare-inregistrare" class="alert alert-danger d-none"></div>
                        <div id="succes-inregistrare" class="alert alert-success d-none"></div>
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" id="reg-email" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Parolă</label>
                            <input type="password" id="reg-parola" class="form-control">
                        </div>
                        <button class="btn btn-primary w-100" onclick="inregistreaza()">Înregistrează-te</button>
                        <p class="text-center mt-3 mb-0">
                            Ai deja cont? <a href="#" onclick="comutaFormular(); return false;">Autentifică-te</a>
                        </p>
                    </div>
                </div>

                <!-- Formularul de autentificare -->
                <div id="form-autentificare" class="card d-none">
                    <div class="card-body">
                        <h5 class="card-title">Autentificare</h5>
                        <div id="eroare-autentificare" class="alert alert-danger d-none"></div>
                        <div class="mb-3">
                            <label class="form-label">Email</label>
                            <input type="email" id="auth-email" class="form-control">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Parolă</label>
                            <input type="password" id="auth-parola" class="form-control">
                        </div>
                        <button class="btn btn-primary w-100" onclick="autentifica()">Conectează-te</button>
                        <p class="text-center mt-3 mb-0">
                            Nu ai cont? <a href="#" onclick="comutaFormular(); return false;">Înregistrează-te</a>
                        </p>
                    </div>
                </div>

            </div>
        </div>
    </div>

    <!-- -------- Sectiunea de sarcini -------- -->
    <div id="sectiune-sarcini" class="d-none">

        <div class="card mb-4">
            <div class="card-body">
                <h5 class="card-title">Adaugă o sarcină</h5>
                <div class="mb-3">
                    <input type="text" id="sarcina-titlu" class="form-control" placeholder="Titlu">
                </div>
                <div class="mb-3">
                    <textarea id="sarcina-descriere" class="form-control" placeholder="Descriere (opțional)" rows="2"></textarea>
                </div>
                <button class="btn btn-success" onclick="adaugaSarcina()">Adaugă</button>
            </div>
        </div>

        <h5>Sarcinile mele</h5>
        <div id="lista-sarcini"></div>

    </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script>
    const API = "http://localhost:8000";

    // -------- Gestionarea token-ului --------

    function salveazaToken(token) {
        localStorage.setItem("token", token);
    }

    function obtineToken() {
        return localStorage.getItem("token");
    }

    function deconecteaza() {
        localStorage.removeItem("token");
        actualizeazaUI();
    }

    // -------- Actualizarea interfetei --------

    function actualizeazaUI() {
        const token = obtineToken();
        if (token) {
            document.getElementById("sectiune-auth").classList.add("d-none");
            document.getElementById("sectiune-sarcini").classList.remove("d-none");
            document.getElementById("info-utilizator").classList.remove("d-none");
            document.getElementById("info-utilizator").classList.add("d-flex");
            try {
                const payload = JSON.parse(atob(token.split(".")[1]));
                document.getElementById("email-utilizator").textContent = payload.sub;
            } catch (e) { /* token malformat */ }
            incarcaSarcini();
        } else {
            document.getElementById("sectiune-auth").classList.remove("d-none");
            document.getElementById("sectiune-sarcini").classList.add("d-none");
            document.getElementById("info-utilizator").classList.add("d-none");
            document.getElementById("info-utilizator").classList.remove("d-flex");
        }
    }

    function comutaFormular() {
        document.getElementById("form-inregistrare").classList.toggle("d-none");
        document.getElementById("form-autentificare").classList.toggle("d-none");
    }

    // -------- Autentificare --------

    async function inregistreaza() {
        ascundeEroare("eroare-inregistrare");
        ascundeEroare("succes-inregistrare");
        const email = document.getElementById("reg-email").value;
        const parola = document.getElementById("reg-parola").value;
        try {
            const raspuns = await fetch(`${API}/inregistrare`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, parola })
            });
            if (!raspuns.ok) {
                const eroare = await raspuns.json();
                afiseazaEroare("eroare-inregistrare", eroare.detail || "Eroare la înregistrare.");
                return;
            }
            afiseazaSucces("succes-inregistrare", "Cont creat! Te poți autentifica.");
            setTimeout(comutaFormular, 1500);
        } catch {
            afiseazaEroare("eroare-inregistrare", "Nu se poate contacta serverul.");
        }
    }

    async function autentifica() {
        ascundeEroare("eroare-autentificare");
        const email = document.getElementById("auth-email").value;
        const parola = document.getElementById("auth-parola").value;
        const dateFormular = new URLSearchParams();
        dateFormular.append("username", email);
        dateFormular.append("password", parola);
        try {
            const raspuns = await fetch(`${API}/autentificare`, {
                method: "POST",
                body: dateFormular
            });
            if (!raspuns.ok) {
                afiseazaEroare("eroare-autentificare", "Email sau parolă incorecte.");
                return;
            }
            const date = await raspuns.json();
            salveazaToken(date.access_token);
            actualizeazaUI();
        } catch {
            afiseazaEroare("eroare-autentificare", "Nu se poate contacta serverul.");
        }
    }

    // -------- Sarcini --------

    async function incarcaSarcini() {
        const token = obtineToken();
        try {
            const raspuns = await fetch(`${API}/sarcini`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (raspuns.status === 401) { deconecteaza(); return; }
            if (!raspuns.ok) return;
            const sarcini = await raspuns.json();
            randeazaSarcini(sarcini);
        } catch {
            document.getElementById("lista-sarcini").innerHTML =
                `<div class="alert alert-warning">Nu se poate contacta serverul.</div>`;
        }
    }

    function randeazaSarcini(sarcini) {
        const container = document.getElementById("lista-sarcini");
        if (sarcini.length === 0) {
            container.innerHTML = `<p class="text-muted">Nicio sarcină adăugată încă.</p>`;
            return;
        }
        container.innerHTML = sarcini.map(s => `
            <div class="card mb-2">
                <div class="card-body d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">
                            ${escapeHtml(s.titlu)}
                            <span class="badge ${s.finalizata ? 'bg-success' : 'bg-secondary'} ms-2">
                                ${s.finalizata ? 'Finalizată' : 'În progres'}
                            </span>
                        </h6>
                        <p class="text-muted small mb-0">${escapeHtml(s.descriere || '')}</p>
                    </div>
                    <div class="d-flex gap-2 ms-3 flex-shrink-0">
                        <button class="btn btn-sm btn-outline-success"
                            onclick="finalizeazaSarcina(${s.id})" ${s.finalizata ? 'disabled' : ''}>
                            Finalizează
                        </button>
                        <button class="btn btn-sm btn-outline-danger" onclick="stergeSarcina(${s.id})">
                            Șterge
                        </button>
                    </div>
                </div>
            </div>
        `).join("");
    }

    async function adaugaSarcina() {
        const titlu = document.getElementById("sarcina-titlu").value.trim();
        if (!titlu) return;
        const token = obtineToken();
        try {
            const raspuns = await fetch(`${API}/sarcini`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    titlu,
                    descriere: document.getElementById("sarcina-descriere").value.trim()
                })
            });
            if (raspuns.ok) {
                document.getElementById("sarcina-titlu").value = "";
                document.getElementById("sarcina-descriere").value = "";
                incarcaSarcini();
            }
        } catch {
            alert("Nu se poate contacta serverul. Verificați că uvicorn rulează.");
        }
    }

    async function finalizeazaSarcina(id) {
        const token = obtineToken();
        try {
            const raspuns = await fetch(`${API}/sarcini/${id}/finaliza`, {
                method: "PATCH",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (raspuns.ok) incarcaSarcini();
        } catch {
            alert("Nu se poate contacta serverul. Verificați că uvicorn rulează.");
        }
    }

    async function stergeSarcina(id) {
        const token = obtineToken();
        try {
            const raspuns = await fetch(`${API}/sarcini/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (raspuns.ok) incarcaSarcini();
        } catch {
            alert("Nu se poate contacta serverul. Verificați că uvicorn rulează.");
        }
    }

    // -------- Utilitare --------

    function afiseazaEroare(elementId, mesaj) {
        const el = document.getElementById(elementId);
        el.textContent = mesaj;
        el.classList.remove("d-none");
    }

    function afiseazaSucces(elementId, mesaj) {
        const el = document.getElementById(elementId);
        el.textContent = mesaj;
        el.classList.remove("d-none");
    }

    function ascundeEroare(elementId) {
        document.getElementById(elementId).classList.add("d-none");
    }

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = String(text);
        return div.innerHTML;
    }

    // -------- Initializare --------
    document.addEventListener("DOMContentLoaded", actualizeazaUI);
</script>
</body>
</html>
```

> **Notă:** Funcția `escapeHtml()` convertește caracterele speciale HTML (`<`, `>`, `&` etc.) din datele utilizatorului în entități sigure înainte de a le insera cu `innerHTML`. Fără această precauție, un titlu de sarcină precum `<script>alert(1)</script>` ar putea executa cod arbitrar - un atac de tip **XSS** (*Cross-Site Scripting*). În aplicații de producție se preferă `createElement()` + `textContent`, dar `escapeHtml()` este o soluție acceptabilă pentru simplitate.

### 7.1 Cum se deschide aplicația

**Metoda recomandată - VS Code Live Server:**
1. Instalați extensia *Live Server* din VS Code (căutați `ritwickdey.liveserver` în Extensions).
2. Click dreapta pe `index.html` în Explorer → *Open with Live Server*.
3. Browserul deschide automat `http://localhost:5500/index.html`.
4. Orice modificare salvată în fișier reîncarcă automat pagina.

**Metoda alternativă - deschidere directă:**
- Dublu-click pe `index.html` în Windows Explorer.
- Browserul deschide fișierul cu protocolul `file://` (originea va fi `"null"`).
- Asigurați-vă că `"null"` este inclus în lista `allow_origins` din `main.py`.

### 7.2 Fluxul de testare recomandat

1. Porniți serverul FastAPI: `uvicorn main:app --reload` (în directorul cu `main.py`).
2. Deschideți `index.html` cu Live Server.
3. Înregistrați un cont nou cu email și parolă.
4. Comutați pe formularul de autentificare (linkul din card) și autentificați-vă.
5. Adăugați 3 sarcini diferite.
6. Finalizați una dintre sarcini - badge-ul trebuie să devină verde, butonul dezactivat.
7. Ștergeți o sarcină.
8. Reîncărcați pagina (`F5`) - sarcinile rămase trebuie să persiste (sunt în baza de date SQLite).
9. Deschideți DevTools (`F12`) → tab-ul **Network**, efectuați o operație și inspectați cererea și răspunsul.
10. Apăsați *Deconectare* - aplicația revine la ecranul de autentificare, tokenul este șters din `localStorage`.

---

## 8. Exercițiu practic: extinderea interfeței

### Cerințe

**A. Editarea unei sarcini existente**

Adăugați în interfață posibilitatea de a edita titlul și descrierea unei sarcini existente. Lângă fiecare sarcină din listă, adăugați un buton "Editează". La apăsarea acestuia, titlul și descrierea sarcinii se transformă în câmpuri de text editabile, pre-completate cu valorile curente. Apare și un buton "Salvează" care apelează `PUT /sarcini/{id}` cu datele modificate, după care lista se reîncarcă.

**B. Filtrul "doar nefinalizate"**

Adăugați un checkbox cu eticheta "Afișează doar sarcinile nefinalizate" deasupra listei de sarcini. Când este bifat, lista se reîncarcă apelând `GET /sarcini?doar_nefinalizate=true`. Când este debifat, se reîncarcă toate sarcinile.

> **Notă:** Cerința B presupune ca endpoint-ul `GET /sarcini` să accepte parametrul de interogare `?doar_nefinalizate=true`. Dacă nu ați implementat această extensie opțională în laboratorul #03, va trebui să o adăugați mai întâi în `main.py`.

### Tabelul endpoint-urilor folosite după implementare

| Operație UI | Metodă | Endpoint | Observații |
|---|---|---|---|
| Înregistrare | POST | `/inregistrare` | Corp JSON |
| Autentificare | POST | `/autentificare` | `URLSearchParams`, returnează JWT |
| Lista sarcini | GET | `/sarcini` | Header `Authorization: Bearer` |
| Creare sarcină | POST | `/sarcini` | Corp JSON |
| Editare sarcină | PUT | `/sarcini/{id}` | Corp JSON, câmpuri parțiale |
| Finalizare sarcină | PATCH | `/sarcini/{id}/finaliza` | Fără corp |
| Ștergere sarcină | DELETE | `/sarcini/{id}` | Fără corp |

### Cod de pornire

Punctul de pornire este aplicația completă din secțiunea 7. Adăugați comentariile TODO de mai jos în locurile indicate:

```javascript
// In functia randeazaSarcini(), in template-ul HTML al fiecarei sarcini,
// langa butoanele existente adaugati:
// TODO A: Un buton "Editeaza" care apeleaza editeazaSarcina(s.id, s.titlu, s.descriere)

// TODO A: Implementati functia editeazaSarcina(id, titluCurent, descriereCurenta):
// - Gasiti elementul card al sarcinii (sau inlocuiti titlul/descrierea cu <input>-uri)
// - Pre-completati campurile cu valorile curente
// - La apasarea "Salveaza", apelati PUT /sarcini/{id} cu noile valori
// - Dupa raspuns ok, apelati incarcaSarcini()
async function editeazaSarcina(id, titluCurent, descriereCurenta) {
    // TODO A: implementati
}

// In functia incarcaSarcini(), inlocuiti linia:
//   const raspuns = await fetch(`${API}/sarcini`, { ... });
// cu:
// TODO B: Verificati daca checkbox-ul "doar-nefinalizate" este bifat.
//         Daca da, adaugati "?doar_nefinalizate=true" la URL.
//         Hint: document.getElementById("doar-nefinalizate").checked
```

De asemenea, adăugați în HTML, înainte de `<h5>Sarcinile mele</h5>`:

```html
<!-- TODO B: Checkbox pentru filtru -->
<div class="form-check mb-3">
    <input class="form-check-input" type="checkbox" id="doar-nefinalizate"
           onchange="incarcaSarcini()">
    <label class="form-check-label" for="doar-nefinalizate">
        Afișează doar sarcinile nefinalizate
    </label>
</div>
```

### Indicații

- Pentru editare inline, cea mai simplă abordare este să regenerați HTML-ul unui singur card: înlocuiți `textContent`-ul titlului cu un `<input type="text">` pre-completat și cel al descrierii cu un `<textarea>`. La click pe "Salvează", citiți `.value` din câmpuri și apelați `PUT`.
- `PUT /sarcini/{id}` așteaptă `Content-Type: application/json`. Trimiteți doar câmpurile `titlu` și `descriere` - modelul `SarcinaActualizare` din Lab #03 accepta câmpuri parțiale, deci `finalizata` nu trebuie inclus.
- `document.getElementById("doar-nefinalizate").checked` returnează `true` sau `false`.
- Construiți URL-ul dinamic:
  ```javascript
  const url = doarNefinalizate ? `${API}/sarcini?doar_nefinalizate=true` : `${API}/sarcini`;
  ```

### Extindere opțională (bonus)

- Adăugați un contor vizibil în navbar de forma "3 sarcini / 1 finalizată", actualizat după fiecare operație. Calculați valorile din array-ul primit de `randeazaSarcini()`.
- Implementați confirmarea ștergerii: înainte de `fetch DELETE`, afișați `window.confirm("Ești sigur că vrei să ștergi această sarcină?")` și continuați doar dacă utilizatorul confirmă.
- Adăugați un câmp de căutare care filtrează sarcinile **pe client** (fără un nou `fetch`) după titlu, folosind `Array.filter()` pe array-ul primit de la server.

---

## Referințe

- [MDN Web Docs: Using the Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [MDN Web Docs: localStorage](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage)
- [MDN Web Docs: Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)
- [MDN Web Docs: Cross-Origin Resource Sharing (CORS)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/CORS)
- [Documentația Bootstrap 5](https://getbootstrap.com/docs/5.3/)
- [LayoutIt! - Bootstrap layout builder](https://www.layoutit.com/)
- [MDN Web Docs: async function / await](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Statements/async_function)
