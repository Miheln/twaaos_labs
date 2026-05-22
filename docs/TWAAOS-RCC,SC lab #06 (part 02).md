# Gemini CLI – Agenți și skill-uri: Laborator practic

> **Cerințe preliminare:** Gemini CLI instalat și autentificat (vezi tutorialul de instalare)

---

## Cuprins

1. [Ce este un agent în Gemini CLI?](#1-ce-este-un-agent-în-gemini-cli)
2. [Sistemul de skill-uri – prezentare generală](#2-sistemul-de-skill-uri--prezentare-generală)
3. [Structura unui skill Markdown](#3-structura-unui-skill-markdown)
4. [Comparație: skill Claude Code vs. skill Gemini CLI](#4-comparație-skill-claude-code-vs-skill-gemini-cli)
5. [Crearea primului tău skill](#5-crearea-primului-tău-skill)
6. [Sistemul de comenzi personalizate (TOML)](#6-sistemul-de-comenzi-personalizate-toml)
7. [Agenți în modul non-interactiv (headless)](#7-agenți-în-modul-non-interactiv-headless)
8. [Exerciții practice](#8-exerciții-practice)

---

## 1. Ce este un agent în Gemini CLI?

În contextul Gemini CLI, termenul **agent** descrie o instanță a modelului Gemini configurată să îndeplinească o sarcină specifică în mod autonom — interacționând cu tool-uri (căutare web, execuție shell, citire fișiere) fără intervenție continuă din partea utilizatorului.

Un agent în Gemini CLI se poate construi pe trei niveluri:

```
┌─────────────────────────────────────────────────────────┐
│  Nivel 3 – AGENT HEADLESS (automatizare completă)       │
│  gemini -p "..." -y --output-format json                │
├─────────────────────────────────────────────────────────┤
│  Nivel 2 – SKILL (comportament specializat reutilizabil)│
│  fișier .md cu frontmatter → invocat cu /skill-name    │
├─────────────────────────────────────────────────────────┤
│  Nivel 1 – COMANDĂ PERSONALIZATĂ (scurtătură de prompt) │
│  fișier .toml în .gemini/commands/ → invocat cu /cmd   │
└─────────────────────────────────────────────────────────┘
```

**Tool-urile built-in** disponibile unui agent Gemini CLI:

| Tool | Descriere |
|---|---|
| `google_web_search` | Caută informații pe web prin Google |
| `web_fetch` | Descarcă și analizează conținutul unei pagini web |
| `read_file` | Citește conținutul unui fișier din workspace |
| `write_file` | Scrie sau modifică fișiere |
| `run_shell_command` | Execută comenzi de sistem |
| `list_directory` | Listează conținutul unui director |

---

## 2. Sistemul de skill-uri – prezentare generală

Gemini CLI a introdus un **sistem de skill-uri bazat pe fișiere Markdown**, conceptual identic cu cel din Claude Code. Un skill este un fișier `.md` cu:

- **Frontmatter YAML** — metadatele skill-ului (nume, descriere, când se folosește)
- **Corp Markdown** — instrucțiunile detaliate pentru model

### Unde se stochează skill-urile

```
~/.gemini/skills/           ← skill-uri globale (disponibile în orice proiect)
    └── deep-researcher.md
    └── code-reviewer.md

<proiect>/.gemini/skills/   ← skill-uri locale (specifice proiectului curent)
    └── analiza-date.md
    └── generare-raport.md
```

> **Regulă de prioritate:** skill-urile locale (din proiect) suprascriu skill-urile globale cu același nume.

### Cum se invocă un skill

În sesiunea interactivă, după ce fișierul există în directorul corect:

```
/deep-researcher Analizează impactul inteligenței artificiale asupra pieței muncii
/code-reviewer
/analiza-date fisier.csv
```

---

## 3. Structura unui skill Markdown

Un fișier de skill are două componente:

### 3.1 Frontmatter YAML (obligatoriu)

```yaml
---
name: numele-skill-ului
description: Descriere scurtă a ce face skill-ul. Include și indicații despre
             când trebuie folosit — de exemplu: "Folosește când utilizatorul
             cere o analiză aprofundată sau un raport structurat."
---
```

**Câmpul `description`** este mai important în Gemini CLI decât în Claude Code — modelul îl folosește pentru a decide automat dacă skill-ul este potrivit pentru cererea curentă. O descriere bună include:
- Ce face skill-ul
- Când trebuie activat (exemple de situații)
- Ce tip de output produce

### 3.2 Corpul Markdown (instrucțiunile agentului)

Corpul fișierului conține instrucțiunile detaliate pe care modelul le urmează când skill-ul este activ. Spre deosebire de un simplu prompt, un skill poate specifica:

- **Workflow-ul pas cu pas** — ce acțiuni să execute și în ce ordine
- **Tool-urile de folosit** — cu nume exacte (`google_web_search`, `web_fetch`)
- **Formatul output-ului** — cum să structureze răspunsul final
- **Bune practici** — reguli specifice domeniului

### 3.3 Anatomia unui skill complet

```markdown
---
name: analizator-cod
description: Analizează calitatea codului sursă, identifică bug-uri potențiale,
             probleme de securitate și oportunități de refactorizare. Folosește
             când utilizatorul cere o recenzie de cod sau un audit tehnic.
---

# Analizator de Cod

Ești un expert în inginerie software cu experiență în revizuirea codului.
Când acest skill este activ, urmezi procedura de mai jos.

## Procedură de analiză

### Pasul 1: Înțelegerea contextului
- Identifică limbajul de programare și framework-ul folosit
- Stabilește scopul modulului/funcției analizate
- Notează dependențele externe

### Pasul 2: Analiza statică
Examinează codul pentru:
- **Bug-uri logice**: condiții greșite, off-by-one errors, cazuri limită netratate
- **Probleme de securitate**: input nevalidat, SQL injection, XSS, credențiale hardcodate
- **Performanță**: algoritmi ineficienți, query-uri N+1, memorie nealocată

### Pasul 3: Calitatea codului
- Respectarea convențiilor de denumire
- Complexitate ciclomatică ridicată (funcții prea lungi sau complicate)
- Cod duplicat (principiul DRY)
- Absența tratării erorilor

### Pasul 4: Raport structurat

Generează raportul în formatul următor:

**Rezumat**: [1-2 propoziții despre starea generală a codului]

**Probleme critice** (blochează funcționarea):
- [ ] descriere problemă + linia de cod + sugestie de remediere

**Probleme majore** (impactează calitatea):
- [ ] ...

**Sugestii de îmbunătățire** (opționale):
- [ ] ...

**Puncte forte**: ce face bine codul analizat
```

---

## 4. Comparație: skill Claude Code vs. skill Gemini CLI

Cele două sisteme sunt aproape identice ca format, dar există diferențe importante de filozofie.

### Exemplu real: skill-ul `deep-researcher`

#### Versiunea Claude Code (`deepresearcher.claudecode.SKILL.md`)

```yaml
---
name: deep-researcher
description: Performs comprehensive, multi-layered research on any topic with
             structured analysis and synthesis of information from multiple sources.
---
```

#### Versiunea Gemini CLI (`deepresearcher.geminicli.SKILL.md`)

```yaml
---
name: deep-researcher
description: Performs comprehensive, multi-layered research on any topic with
             structured analysis and synthesis of information from multiple sources.
             Use when the user needs deep investigation into a topic, market research,
             technical due diligence, or structured reports based on diverse
             information sources.
---
```

### Tabel comparativ al diferențelor

| Aspect | Claude Code | Gemini CLI |
|---|---|---|
| Format fișier | `.md` cu frontmatter YAML | `.md` cu frontmatter YAML |
| Director global | `~/.claude/skills/` | `~/.gemini/skills/` |
| Director local | `.claude/skills/` | `.gemini/skills/` |
| Invocare | `/skill-name [args]` | `/skill-name [args]` |
| Câmpuri frontmatter | `name`, `description` | `name`, `description` (mai detaliat) |
| Referință la tool-uri | Nu (implicit) | Da — explicit (`google_web_search`, `web_fetch`) |
| Descriere frontmatter | Scurtă, ce face | Lungă — include și **când** se folosește |
| Verbose vs. concis | Mai verbose, tip tutorial | Mai concis, orientat pe acțiune |

### Diferența esențială: descrierea frontmatter-ului

În **Claude Code**, descrierea este scurtă și generică:
```yaml
description: Performs comprehensive, multi-layered research on any topic.
```

În **Gemini CLI**, descrierea include explicit condițiile de activare:
```yaml
description: Performs comprehensive research... Use when the user needs deep
             investigation into a topic, market research, technical due diligence,
             or structured reports based on diverse information sources.
```

**De ce contează?** Gemini CLI folosește descrierea pentru **routing automat** — modelul poate decide să activeze un skill fără ca utilizatorul să îl invoce explicit, dacă cererea corespunde descrierii.

### Diferența în corpul skill-ului: referința la tool-uri

**Claude Code** — nu menționează tool-uri specifice (modelul decide); exemplificare:
```markdown
## Step 2: Conduct initial exploratory research
Begin with broad reconnaissance to map the landscape:
- **Search for overview information**: Use search tools to find general information...
```

**Gemini CLI** — specifică explicit ce tool să folosească; exemplificare:
```markdown
### Step 2: Exploratory Research
- Use `google_web_search` for broad reconnaissance.
- Identify authoritative sources, recent publications, and expert opinions.
- Use `web_fetch` to analyze high-quality sources in depth.
```

Această explicitare îmbunătățește consistența comportamentului agentului — știe exact cu ce tool să execute fiecare pas.

---

## 5. Crearea primului skill

### Exercițiu ghidat: skill de sumarizare a știrilor

#### Pasul 1: Creează directorul de skill-uri

```bash
# skill-uri globale (recomandat pentru uz personal)
mkdir -p ~/.gemini/skills

# sau skill-uri locale pentru proiectul curent
mkdir -p .gemini/skills
```

#### Pasul 2: Creează fișierul skill-ului

```bash
# Windows (PowerShell)
New-Item ~/.gemini/skills/news-summary.md

# Linux / macOS
touch ~/.gemini/skills/news-summary.md
```

#### Pasul 3: Scrie conținutul skill-ului

Deschide fișierul `~/.gemini/skills/news-summary.md` și adaugă:

```markdown
---
name: news-summary
description: Caută și rezumă știrile recente despre un subiect dat. Folosește
             când utilizatorul vrea să afle ce s-a întâmplat recent legat de
             un topic sau eveniment. Produce un rezumat structurat cu surse.
---

# Sumarizator de Știri

Ești un jurnalist specializat în rezumarea rapidă a informațiilor din surse multiple.

## Procedură

### Pasul 1: Căutare inițială
Folosește `google_web_search` pentru a căuta știri recente despre subiectul primit.
Formulează cel puțin 2-3 căutări cu unghiuri diferite:
- Căutare generală: "[subiect] news [luna curentă] [an]"
- Căutare aprofundată: "[subiect] latest developments"
- Căutare de reacții: "[subiect] expert opinion"

### Pasul 2: Extragerea detaliilor
Pentru cele mai relevante 3-4 surse găsite, folosește `web_fetch` pentru a citi
conținutul complet și a extrage informații detaliate.

### Pasul 3: Sinteza

Produce rezumatul în formatul următor:

---
## Rezumat: [Subiect] — [Data curentă]

**Ce s-a întâmplat** (2-3 propoziții cu esențialul)

**Detalii importante:**
- Punct cheie 1
- Punct cheie 2
- Punct cheie 3

**Context:** [Informații de fundal necesare pentru înțelegere]

**Ce urmează:** [Evoluții așteptate sau de urmărit]

**Surse consultate:**
1. [Titlu sursă](URL)
2. ...
---

## Reguli
- Prezintă faptele obiectiv, fără opinie personală
- Menționează întotdeauna sursele
- Dacă informațiile sunt contradictorii, menționează ambele versiuni
- Prioritizează sursele de știri reputate față de bloguri sau rețele sociale
```

#### Pasul 4: Testează skill-ul

Deschide Gemini CLI și invocă skill-ul:

```
gemini
> /news-summary inteligență artificială în educație
```

Gemini CLI va căuta automat, va analiza sursele și va produce rezumatul structurat.

---

## 6. Sistemul de comenzi personalizate (TOML)

Pe lângă skill-urile Markdown, Gemini CLI oferă un sistem de **comenzi personalizate** bazate pe fișiere TOML — mai potrivite pentru scurtături de prompt-uri fixe sau acțiuni cu argumente simple.

### Diferența față de skill-uri

| Caracteristică | Skill (Markdown) | Comandă personalizată (TOML) |
|---|---|---|
| Format | `.md` cu YAML frontmatter | `.toml` |
| Director | `.gemini/skills/` | `.gemini/commands/` |
| Scop | Comportament complex, multi-pas | Scurtătură de prompt simplu |
| Argumente | Flexibile, procesate de model | `$args`, `!{shell}`, `@{file}` |
| Execuție shell | Prin tool-ul run_shell_command | Nativ cu `!{...}` |
| Injectare fișiere | Prin tool-ul read_file | Nativ cu `@{...}` |

### Structura unui fișier TOML

```toml
# ~/.gemini/commands/git-commit.toml

description = "Generează un mesaj de commit pe baza modificărilor staged."

prompt = """
Analizează diff-ul următor și scrie un mesaj de commit concis și descriptiv.
Urmează formatul Conventional Commits (feat:, fix:, docs:, refactor:, etc.).
Mesajul trebuie să explice CE s-a schimbat și DE CE, nu HOW.

Diff:
```diff
!{git diff --staged}
```

Scrie DOAR mesajul de commit, fără explicații suplimentare.
"""
```

Invocare:
```
> /git-commit
```

### Comenzi cu argumente

```toml
# ~/.gemini/commands/explica.toml

description = "Explică un concept tehnic pe înțelesul unui student."

prompt = """
Explică conceptul următor pe înțelesul unui student de informatică din anul I.
Folosește analogii din viața reală și exemple de cod simple.
Conceptul de explicat: $args
"""
```

Invocare:
```
> /explica recursivitate
> /explica ce este un pointer în C
```

### Namespacing cu subdirectoare

Subdirectoarele creează comenzi grupate cu prefixul `:`:

```
.gemini/commands/
├── git/
│   ├── commit.toml      → /git:commit
│   ├── review.toml      → /git:review
│   └── changelog.toml   → /git:changelog
├── doc/
│   ├── readme.toml      → /doc:readme
│   └── api.toml         → /doc:api
└── analiza.toml         → /analiza
```

### Injectare de fișiere cu `@{...}`

```toml
# .gemini/commands/review-pr.toml

description = "Revizuiește un Pull Request față de ghidul de contribuție."

prompt = """
Revizuiește codul următor față de standardele proiectului nostru:

Ghid de contribuție:
@{CONTRIBUTING.md}

Codul de revizuit: $args

Verifică:
1. Respectarea convențiilor de cod din ghid
2. Teste unitare prezente și acoperire suficientă
3. Documentație actualizată
4. Breaking changes identificate
"""
```

---

## 7. Agenți în modul non-interactiv (headless)

Modul headless permite rularea unui agent Gemini CLI ca parte dintr-un script, pipeline CI/CD sau task automatizat — fără interacțiune umană.

### Anatomia unui agent headless

```bash
gemini \
  --prompt "Instrucțiunea agentului" \
  --model gemini-2.5-pro \
  --yolo \
  --output-format json
```

**Flag-urile esențiale:**

| Flag | Efect |
|---|---|
| `-p` / `--prompt` | Activează modul headless + transmite instrucțiunea |
| `-y` / `--yolo` | Aprobă automat toate acțiunile tool-urilor (fără prompt interactiv) |
| `--output-format json` | Returnează răspunsul ca JSON structurat (ușor de parsat) |
| `-m` / `--model` | Specifică modelul (ex: `gemini-2.5-flash` pentru viteză) |
| `--all-files` | Include toate fișierele din directorul curent în context |

### Exemple de agenți headless

#### Agent de analiză a log-urilor

```bash
#!/bin/bash
# analiza-loguri.sh

LOG_FILE="/var/log/app/error.log"
RAPORT="raport-$(date +%Y%m%d).md"

cat "$LOG_FILE" | gemini \
  -p "Analizează aceste log-uri de eroare. Identifică erorile recurente,
      grupează-le pe categorii și sugerează soluții pentru cele mai frecvente.
      Formatul răspunsului: Markdown cu secțiuni clare." \
  -m gemini-2.5-flash \
  > "$RAPORT"

echo "Raport generat: $RAPORT"
```

#### Agent de generare a mesajelor de commit

```bash
#!/bin/bash
# smart-commit.sh

DIFF=$(git diff --cached)

if [ -z "$DIFF" ]; then
    echo "Nu există modificări staged."
    exit 1
fi

MESAJ=$(echo "$DIFF" | gemini \
  -p "Scrie un mesaj de commit în format Conventional Commits.
      Răspunde DOAR cu mesajul de commit, nimic altceva." \
  --output-format json | jq -r '.response')

echo "Mesaj propus: $MESAJ"
read -p "Confirmi? (y/n): " CONFIRMARE

if [ "$CONFIRMARE" = "y" ]; then
    git commit -m "$MESAJ"
fi
```

#### Agent de monitorizare și alertare (Windows PowerShell)

```powershell
# monitor-site.ps1

$URL = "https://exemplu.com"
$REZULTAT = Invoke-WebRequest -Uri $URL -TimeoutSec 10 -ErrorAction SilentlyContinue

$STARE = if ($REZULTAT.StatusCode -eq 200) { "OK" } else { "EROARE" }
$CONTINUT = $REZULTAT.Content | Select-String -Pattern "eroare|error|down" -AllMatches

$ANALIZA = "$STARE`nConținut: $($CONTINUT.Matches.Count) mențiuni de erori" |
    gemini -p "Pe baza acestui raport de monitorizare, determină dacă există
               o problemă critică și ce acțiune recomandă. Răspuns în 2 propoziții." |
    Out-String

Write-Host $ANALIZA
```

#### Agent de cercetare cu output JSON și procesare ulterioară

```bash
#!/bin/bash
# cercetare-competitori.sh

SUBIECT="$1"

if [ -z "$SUBIECT" ]; then
    echo "Utilizare: $0 <subiect>"
    exit 1
fi

REZULTAT=$(gemini \
  -p "Cercetează subiectul: '$SUBIECT'.
      Găsește 5 surse relevante, extrage informațiile cheie și
      sintetizează un rezumat de 200 de cuvinte cu concluzii practice." \
  -m gemini-2.5-pro \
  --output-format json)

# Extrage răspunsul și statisticile
RASPUNS=$(echo "$REZULTAT" | jq -r '.response')
TOKENI=$(echo "$REZULTAT" | jq -r '.stats.models | to_entries[0].value.tokens.total // "N/A"')

echo "=== Raport: $SUBIECT ==="
echo "$RASPUNS"
echo ""
echo "--- Tokeni consumați: $TOKENI ---"

# Salvează în fișier
echo "$RASPUNS" > "cercetare-${SUBIECT// /-}.md"
```

### Agent headless cu context din fișiere locale

```bash
# Analizează toate fișierele Python dintr-un proiect
gemini \
  --all-files \
  -p "Revizuiește codul din acest proiect Python.
      Identifică problemele de securitate, anti-pattern-urile și
      oportunitățile de optimizare. Generează un raport structurat." \
  --output-format json \
  > audit-cod.json

# Extrage doar răspunsul
jq -r '.response' audit-cod.json > audit-cod.md
```

### Integrare în GitHub Actions

```yaml
# .github/workflows/code-review.yml
name: Code Review automat

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Instalare Gemini CLI
        run: npm install -g @google/gemini-cli

      - name: Code Review automat
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          DIFF=$(git diff origin/main...HEAD)
          REVIEW=$(echo "$DIFF" | gemini \
            -p "Revizuiește modificările din acest Pull Request.
                Identifică bug-uri potențiale, probleme de securitate
                și sugestii de îmbunătățire." \
            --output-format json | jq -r '.response')

          echo "## 🤖 Code Review automat" >> $GITHUB_STEP_SUMMARY
          echo "$REVIEW" >> $GITHUB_STEP_SUMMARY
```

---

## 8. Exerciții practice

### Exercițiul 1 — Skill simplu (30 minute)

Creează un skill `traductor.md` care:
- Detectează automat limba textului primit
- Traduce în română dacă textul e în altă limbă, sau în engleză dacă e deja în română
- Păstrează formatarea originală (Markdown, cod, liste)

Fișierul va fi plasat în `~/.gemini/skills/traductor.md`.

**Test:**
```
> /traductor The quick brown fox jumps over the lazy dog
> /traductor Aceasta este o propoziție de test în română
```

---

### Exercițiul 2 — Comandă personalizată TOML (20 minute)

Creează comanda `/doc:functie` care primește numele unei funcții ca argument și:
1. Caută funcția în fișierele `.py` din directorul curent
2. Generează documentație în format docstring Google Style

Structura fișierului: `.gemini/commands/doc/functie.toml`

**Test** (dintr-un director cu cod Python):
```
> /doc:functie calculeaza_media
```

---

### Exercițiul 3 — Agent headless (40 minute)

Scrie un script `raport-zilnic.sh` (Linux/macOS) sau `raport-zilnic.ps1` (Windows) care:
1. Citește fișierele modificate azi din directorul curent (`git diff --name-only HEAD~1`)
2. Trimite lista către Gemini cu instrucțiunea de a genera un rezumat al muncii din zi
3. Salvează output-ul în `rapoarte/YYYY-MM-DD.md`
4. Afișează numărul de tokeni consumați

**Bonus:** adaugă o verificare care să nu execute dacă nu există modificări git.

---

### Exercițiul 4 — Conversie skill din Claude Code (30 minute)

Ia un skill de Claude Code existent (sau unul inventat de tine) și convertește-l pentru Gemini CLI. Aplică regulile de conversie:

1. **Îmbogățește descrierea frontmatter-ului** — adaugă clauza „Use when..."
2. **Referențiază tool-urile explicit** — înlocuiește formulările vagi cu `google_web_search`, `web_fetch`, etc.
3. **Elimină redundanțele** — skill-urile Gemini sunt mai concise; elimină repetițiile
4. **Testează** — invocă skill-ul convertit și compară comportamentul

---

## Rezumat

| Concept | Format | Locație | Invocare |
|---|---|---|---|
| Skill | `.md` + YAML frontmatter | `.gemini/skills/` | `/skill-name` |
| Comandă personalizată | `.toml` | `.gemini/commands/` | `/comanda` sau `/grup:comanda` |
| Context de proiect | `GEMINI.md` | rădăcina proiectului | automat |
| Agent headless | script shell/PS | oriunde | `gemini -p "..." -y` |

**Principii cheie:**
- Skill-urile Gemini au descrieri mai detaliate decât cele Claude Code — includ condițiile de activare
- Tool-urile se referențiază explicit în corpul skill-ului (`google_web_search`, `web_fetch`)
- Comenzile TOML sunt mai potrivite pentru scurtături cu argumente fixe și execuție shell
- Flag-ul `-y` (yolo) este obligatoriu în agenții headless — altfel execuția se blochează la confirmări interactive

---

*Referințe:*
- *Documentație oficială comenzi: https://google-gemini.github.io/gemini-cli/docs/cli/commands.html*
- *Custom commands: https://google-gemini.github.io/gemini-cli/docs/cli/custom-commands.html*
- *Headless mode: https://google-gemini.github.io/gemini-cli/docs/cli/headless.html*
