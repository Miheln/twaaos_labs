# Gemini CLI – Tutorial de instalare și utilizare

> Documentație de referință: https://google-gemini.github.io/gemini-cli/docs/cli/commands.html

---

## Cuprins

1. [Cerințe preliminare](#1-cerințe-preliminare)
2. [Instalare](#2-instalare)
3. [Autentificare](#3-autentificare)
4. [Pornire și interfața interactivă](#4-pornire-și-interfața-interactivă)
5. [Comenzi slash (/)](#5-comenzi-slash-)
6. [Comenzi @ – includerea fișierelor](#6-comenzi----includerea-fișierelor)
7. [Comenzi ! – execuție shell](#7-comenzi----execuție-shell)
8. [Modul non-interactiv (headless)](#8-modul-non-interactiv-headless)
9. [Variabile de mediu utile](#9-variabile-de-mediu-utile)
10. [Fișierul GEMINI.md](#10-fișierul-geminimd)

---

## 1. Cerințe preliminare

### Node.js

Gemini CLI necesită **Node.js 18 LTS sau mai nou** (recomandat: 20 LTS sau 22 LTS).

Verificare versiune existentă:

```bash
node --version
npm --version
```

#### Instalare Node.js (dacă nu este prezent)

**Windows** – descarcă installerul de pe https://nodejs.org sau folosește winget:

```powershell
winget install OpenJS.NodeJS.LTS
```

**Linux (Ubuntu/Debian)** – via NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

**Linux (fedora/RHEL):**

```bash
sudo dnf install nodejs
```

**macOS** – via Homebrew:

```bash
brew install node
```

---

## 2. Instalare

### Varianta 1 – Instalare globală (recomandată)

Instalează pachetul o singură dată; comanda `gemini` devine disponibilă în orice locație:

```bash
npm install -g @google/gemini-cli
```

Verificare instalare:

```bash
gemini --version
```

### Varianta 2 – Execuție directă cu npx (fără instalare)

Rulează întotdeauna cea mai recentă versiune, fără a ocupa spațiu global:

```bash
npx @google/gemini-cli
```

### Varianta 3 – Execuție directă din GitHub

```bash
npx https://github.com/google-gemini/gemini-cli
```

### Varianta 4 – Instalare în sandbox Docker

```bash
gemini --sandbox -y -p "promptul tău"
```

> **Recomandare:** folosește varianta 1 (instalare globală) pentru utilizare zilnică și varianta 2 (npx) dacă vrei să testezi fără a instala.

---

## 3. Autentificare

La prima pornire, Gemini CLI solicită o metodă de autentificare. Există patru opțiuni:

### Opțiunea A – Cont Google (recomandat pentru uz personal)

Cea mai simplă metodă. CLI deschide un browser pentru autentificare; credențialele sunt salvate local pentru sesiunile viitoare.

```bash
gemini
# → selectează "Login with Google" din meniu
```

Opțional, pentru conturi Google Workspace sau regiuni restricționate:

```bash
export GOOGLE_CLOUD_PROJECT="ID-ul-proiectului-tau"
```

### Opțiunea B – API Key Gemini (prototipuri rapide)

1. Generează o cheie API din [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Setează variabila de mediu:

```bash
export GEMINI_API_KEY="cheia-ta-api"
```

Sau adaug-o permanent în `~/.gemini/.env`:

```
GEMINI_API_KEY=cheia-ta-api
```

### Opțiunea C – Vertex AI cu gcloud (mașini de dezvoltare)

```bash
gcloud auth application-default login
export GOOGLE_CLOUD_PROJECT="proiectul-tau"
export GOOGLE_CLOUD_LOCATION="us-central1"
# dezactivează alte chei dacă există:
unset GOOGLE_API_KEY GEMINI_API_KEY
```

### Opțiunea D – Service Account JSON (CI/CD, automatizări)

Cea mai potrivită pentru medii non-interactive (servere, pipeline-uri):

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/cale/catre/keyfile.json"
export GOOGLE_CLOUD_PROJECT="proiectul-tau"
export GOOGLE_CLOUD_LOCATION="us-central1"
```

Contul de serviciu trebuie să aibă rolul **Vertex AI User** în Google Cloud.

### Persistarea credențialelor

**Fișier shell** (`~/.bashrc`, `~/.zshrc`, sau PowerShell profile):

```bash
echo 'export GEMINI_API_KEY="cheia-ta"' >> ~/.bashrc
source ~/.bashrc
```

**Fișier `.env`** (prioritate față de cel din home):

```
# ~/.gemini/.env
GEMINI_API_KEY=cheia-ta-api
GOOGLE_CLOUD_PROJECT=proiectul-tau
```

| Metodă | Mediu | Recomandare |
|---|---|---|
| Google Login | Interactiv, local | Utilizatori individuali |
| API Key | Orice | Prototipuri, testare rapidă |
| Vertex AI ADC | Mașini cu gcloud | Dezvoltatori GCP |
| Service Account | Non-interactiv | CI/CD, servere, automatizări |

---

## 4. Pornire și interfața interactivă

```bash
gemini
```

Se deschide un REPL interactiv în care poți scrie prompt-uri direct. La prima rulare se parcurge și configurarea inițială (autentificare, model implicit).

**Flag-uri utile la pornire:**

```bash
gemini --model gemini-2.5-pro        # specifică modelul
gemini --debug                       # activează log-uri verbose
gemini --all-files                   # include toate fișierele din directorul curent în context
gemini --include-directories src,docs  # include directoare specifice
```

---

## 5. Comenzi slash (/)

Comenzile slash sunt disponibile în modul interactiv și oferă control asupra sesiunii. Se introduc direct în prompt.

### Navigare și ajutor

| Comandă | Descriere |
|---|---|
| `/help` sau `/?` | Afișează lista tuturor comenzilor disponibile |
| `/about` | Versiunea curentă a Gemini CLI |
| `/quit` sau `/exit` | Închide sesiunea |

### Gestionarea conversației

| Comandă | Descriere |
|---|---|
| `/clear` | Șterge ecranul (echivalent Ctrl+L) |
| `/compress` | Înlocuiește contextul curent cu un rezumat — economisește tokeni în conversații lungi |
| `/copy` | Copiază ultimul răspuns al modelului în clipboard |
| `/stats` | Afișează statistici de sesiune: tokeni consumați, durată, modele utilizate |

### Salvarea și reluarea conversațiilor

```
/chat save    <nume>    – salvează starea curentă a conversației
/chat resume  <nume>    – reia o conversație salvată anterior
/chat list              – listează toate conversațiile salvate
/chat delete  <nume>    – șterge o conversație salvată
/chat share             – generează un link de partajare
```

### Gestionarea memoriei (GEMINI.md)

```
/memory show            – afișează conținutul instrucțiunilor memorate
/memory add   <text>    – adaugă o instrucțiune permanentă în GEMINI.md
/memory refresh         – reîncarcă fișierele GEMINI.md din disc
/memory list            – listează fișierele GEMINI.md active
```

### Workspace și fișiere

```
/directory add  <cale>  – adaugă un director în workspace-ul curent
/directory show         – afișează directoarele active
/restore                – readuce fișierele la starea dinaintea ultimei operații a unui tool
```

### MCP și extensii

```
/mcp                    – listează serverele MCP conectate, starea și tool-urile disponibile
/extensions             – listează extensiile active în sesiunea curentă
/tools                  – listează toate tool-urile disponibile (built-in + MCP)
```

### Configurare și aspect

```
/settings               – deschide editorul de configurare
/theme                  – schimbă tema vizuală a interfeței
/editor                 – selectează editorul extern (pentru fișiere mari)
/auth                   – schimbă metoda de autentificare pentru sesiunea curentă
/vim                    – activează modul vim (moduri NORMAL și INSERT în prompt)
```

### Altele

```
/init                   – generează un fișier GEMINI.md personalizat pentru proiectul curent
/privacy                – afișează notificarea de confidențialitate
/bug <titlu>            – deschide un issue nou pe repository-ul Gemini CLI
```

---

## 6. Comenzi @ – includerea fișierelor

Prefixul `@` injectează conținutul unui fișier sau director direct în prompt, fără a-l copia manual.

```bash
# include un fișier specific
@src/main.py Explică ce face această funcție

# include un director întreg
@src/ Identifică problemele de securitate din acest cod

# include mai multe fișiere simultan
@README.md @package.json Care sunt dependențele proiectului?
```

> **Notă:** fișierele listate în `.gitignore` sunt excluse automat. Folosește `--all-files` la pornire pentru a le include.

---

## 7. Comenzi ! – execuție shell

Prefixul `!` execută o comandă de sistem și returnează rezultatul în context.

```bash
# execuție unică
!ls -la
!git log --oneline -10
!cat package.json

# toggle mod shell interactiv (toate comenzile sunt executate ca shell)
!
```

Variabila de mediu `GEMINI_CLI=1` este setată automat pentru subprocesele lansate din Gemini CLI, util pentru a detecta contextul în scripturi.

---

## 8. Modul non-interactiv (headless)

Gemini CLI poate fi rulat complet fără interfață interactivă — util pentru scripturi, pipeline-uri CI/CD și automatizări.

### Flag-uri headless

| Flag | Prescurtat | Descriere |
|---|---|---|
| `--prompt <text>` | `-p` | Activează modul headless cu promptul dat |
| `--output-format <format>` | | Format ieșire: `text` (implicit) sau `json` |
| `--model <model>` | `-m` | Specifică modelul (ex: `gemini-2.5-flash`) |
| `--yolo` | `-y` | Aprobă automat toate acțiunile tool-urilor |
| `--approval-mode <mod>` | | Modul de aprobare: `auto_edit` etc. |
| `--all-files` | `-a` | Include toate fișierele din directorul curent |
| `--include-directories` | | Include directoare suplimentare: `src,docs` |
| `--debug` | `-d` | Activează log-uri verbose |
| `--sandbox` | | Rulează în container izolat |

### Metode de input

```bash
# 1. Prompt ca argument
gemini -p "Explică ce este o funcție recursivă"

# 2. Stdin prin pipe
echo "Rezumă acest text: ..." | gemini

# 3. Fișier prin pipe + instrucțiune
cat raport.txt | gemini -p "Extrage acțiunile principale din acest raport"

# 4. Combinat: fișier + instrucțiune + model specific
cat eroare.log | gemini -p "Care este cauza acestei erori?" -m gemini-2.5-flash
```

### Output în format JSON

Formatul JSON returnează un obiect structurat cu răspunsul și metadate:

```bash
gemini -p "Generează 3 idei de proiect" --output-format json
```

Structura răspunsului JSON:

```json
{
  "response": "textul generat de model",
  "stats": {
    "models": {
      "gemini-2.5-flash": {
        "tokens": { "input": 120, "output": 340, "total": 460 }
      }
    }
  },
  "error": null
}
```

### Exemple de scripturi

**Generare automată de mesaje de commit:**

```bash
#!/bin/bash
result=$(git diff --cached | gemini -p "Scrie un mesaj de commit concis pentru aceste modificări" --output-format json)
mesaj=$(echo "$result" | jq -r '.response')
git commit -m "$mesaj"
```

**Analiză batch a fișierelor Python:**

```bash
#!/bin/bash
mkdir -p rapoarte
for fisier in src/*.py; do
    echo "Analizez: $fisier"
    cat "$fisier" | gemini -p "Identifică bug-uri și probleme de calitate" \
        --output-format json \
        > "rapoarte/$(basename "$fisier").json"
done
```

**Extragerea răspunsului din JSON cu jq:**

```bash
gemini -p "Lista 5 limbaje de programare populare" --output-format json | jq -r '.response'
```

**Salvare output în fișier:**

```bash
gemini -p "Scrie documentație pentru API-ul de mai jos" > docs/api.md
```

**Append la un fișier existent:**

```bash
gemini -p "Adaugă secțiunea de FAQ" >> docs/readme.md
```

**Monitorizarea consumului de tokeni:**

```bash
result=$(gemini -p "query" --output-format json)
tokeni=$(echo "$result" | jq -r '.stats.models | to_entries[0].value.tokens.total')
echo "Tokeni consumați: $tokeni"
```

**Pipeline CI/CD (GitHub Actions):**

```yaml
- name: Code Review automat
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  run: |
    git diff origin/main...HEAD | gemini -p "Identifică probleme de securitate sau calitate" \
      --output-format json | jq -r '.response' >> $GITHUB_STEP_SUMMARY
```

---

## 9. Variabile de mediu utile

| Variabilă | Descriere |
|---|---|
| `GEMINI_API_KEY` | Cheia API pentru autentificare directă |
| `GOOGLE_CLOUD_PROJECT` | ID-ul proiectului Google Cloud |
| `GOOGLE_CLOUD_LOCATION` | Regiunea Vertex AI (ex: `us-central1`) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Calea către fișierul JSON al contului de serviciu |
| `GEMINI_CLI=1` | Setată automat de CLI pentru subprocese — util pentru detecția contextului |

---

## 10. Fișierul GEMINI.md

Similar cu `CLAUDE.md` din Claude Code, fișierul `GEMINI.md` conține instrucțiuni permanente pentru model — context de proiect, convenții, restricții.

**Locații căutate (în ordine):**

1. `~/.gemini/GEMINI.md` — instrucțiuni globale (pentru toate proiectele)
2. `GEMINI.md` în rădăcina proiectului curent

**Generare automată pentru proiectul curent:**

```bash
# în modul interactiv:
/init
```

**Exemplu de conținut:**

```markdown
# Proiect: API Backend

## Context
Acest proiect este un REST API scris în Python (FastAPI).
Baza de date este PostgreSQL, ORM-ul folosit este SQLAlchemy.

## Convenții
- Răspunsurile să fie în limba română
- Comentariile din cod în engleză
- Nu sugera dependențe noi fără a justifica nevoia

## Restricții
- Nu modifica fișierele din directorul /migrations direct
```

---

## Referințe

- Documentație oficială comenzi: https://google-gemini.github.io/gemini-cli/docs/cli/commands.html
- Headless mode: https://google-gemini.github.io/gemini-cli/docs/cli/headless.html
- Autentificare: https://google-gemini.github.io/gemini-cli/docs/get-started/authentication.html
- Repository GitHub: https://github.com/google-gemini/gemini-cli
- Google AI Studio (API Keys): https://aistudio.google.com/app/apikey
