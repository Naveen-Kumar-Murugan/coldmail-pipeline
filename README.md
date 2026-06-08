<div align="center">

### **Automated Cold-Outreach Pipeline**
*One domain in → Lookalike companies → Decision-makers → Verified emails → Outreach sent*

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Ocean.io](https://img.shields.io/badge/Ocean.io-Lookalike_Search-00b4d8?style=for-the-badge)](https://ocean.io)
[![Prospeo](https://img.shields.io/badge/Prospeo-Contact_Search-6c8ef5?style=for-the-badge)](https://prospeo.io)
[![Eazyreach](https://img.shields.io/badge/Eazyreach-Email_Resolve-4ade80?style=for-the-badge)](https://eazyreach.app)
[![Brevo](https://img.shields.io/badge/Brevo-Email_Sending-0b996e?style=for-the-badge)](https://brevo.com)


</div>

---

## 📺 Demo

> 🎬 **[Watch the Live Demo →](https://drive.google.com/file/d/1wxLQWqhP3FWznooahbXjYnGQpj3mufRz/view?usp=sharing)**

<br/>

---

## 📸 Screenshots

<br/>

> **Dashboard**
>![alt text](<Screenshot 2026-06-08 at 11.41.15 AM.png>)

> **CLI Mode — Rich Terminal Output**
>![alt text](<Screenshot 2026-06-08 at 11.41.37 AM.png>)

<br/>

---

## 🗂️ Table of Contents

- [What This Is](#-what-this-is)
- [How It Works — The 4-Stage Pipeline](#-how-it-works--the-4-stage-pipeline)
- [Project Architecture](#-project-architecture)
- [File Structure](#-file-structure)
- [Domain & Sender Setup](#-domain--sender-setup-navdevxyz)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running the Pipeline](#-running-the-pipeline)
- [Web Dashboard](#-web-dashboard)
- [Error Handling & Resilience](#-error-handling--resilience)
- [Checkpoint System](#-checkpoint-system)
- [Rate Limiting & Retry Logic](#-rate-limiting--retry-logic)
- [Email Copywriting](#-email-copywriting)
- [API Reference Summary](#-api-reference-summary)
- [Tech Stack](#-tech-stack)

---

## 🚀 What This Is

Coldmail Outreach Pipeline is a **fully automated, zero-human-in-the-loop cold outreach system**. You type one company domain. The pipeline does everything else finding similar companies, hunting down their decision-makers, resolving their verified work emails, and sending each of them a personalised cold email.

It runs in two modes:

| Mode | Command | Description |
|---|---|---|
| **CLI** | `python main.py stripe.com` | Rich terminal output, progress bars, tables |
| **Web Dashboard** | `python main.py --ui` | Flask + SSE live dashboard in your browser |

Both modes share exactly the same pipeline engine underneath.

---

## ⚙️ How It Works — The 4-Stage Pipeline

```
  You type one domain
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│   ① Ocean.io          ② Prospeo            ③ Enricher       ④ Brevo  |
│                                                                         │
│   seed.com    ──►  [company.com,   ──►  [jane@acme.com, ──►  📧 Sent    │
│   (1 domain)       acme.com, ...]       bob@beta.io ...]                │
│                                                                         │
│   Lookalike        Decision-maker        Email resolution    Outreach   │
│   discovery        search                (Eazyreach → Prospeo)  send    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
         │
         ▼
  ⚠️  Safety checkpoint before Stage 4 fires
  (CLI prompt or web modal — you confirm before a single email is sent)
```

### Stage 1 · Ocean.io — Lookalike Company Discovery

**Input:** One seed domain (e.g. `stripe.com`)
**Output:** List of 5–50 similar company domains

The pipeline hits Ocean.io's `/v3/search/companies` endpoint with `lookalikeDomains: [seed]`. It filters out junk domains (social media, `.gov`, `.edu`, no-TLD strings), deduplicates, and excludes the seed domain itself.

```
stripe.com  →  [braintree.com, adyen.com, mollie.com, checkout.com, ...]
```

---

### Stage 2 · Prospeo — Decision-Maker Search

**Input:** List of company domains from Stage 1
**Output:** List of contacts (name, title, company, LinkedIn URL, `person_id`) — **no emails yet**

For each domain, Prospeo's `/search-person` endpoint is called with seniority filters targeting `C-Suite`, `VP`, `Founder/Owner`, and `Director`. A configurable cap (`PROSPEO_MAX_PER_COMPANY`, default: 3) limits how many contacts are pulled per company to protect credits.

Contacts are deduplicated across companies by both `person_id` and `linkedin_url` before passing to Stage 3.

---

### Stage 3 · Email Enrichment — Eazyreach Primary, Prospeo Fallback

**Input:** Contacts list with `person_id` / `linkedin_url` but no email
**Output:** Same list with `email` and `email_status` populated

> ⚠️ **Important:** Eazyreach is the **primary** email resolver. Prospeo `/enrich-person` is the **fallback** used only when Eazyreach fails, returns no result, or its API is unavailable.

**Resolution priority:**

```
For each contact:
  1. Try Eazyreach  →  resolve LinkedIn URL → verified work email
       ↓ (on failure / NotImplementedError / no result)
  2. Fall back to Prospeo /enrich-person  →  email via person_id or linkedin_url
       ↓ (if no verified email found)
  3. Mark contact email_status = "NOT_FOUND"  →  skip in Stage 4
```

Contacts without a resolved email are **kept in the dataset** (for audit) but skipped during sending. You are never charged for a Prospeo enrich that returns no email (`only_verified_email: true`).

> **File:** `pipeline/stage3_enricher.py`

---

### Stage 4 · Brevo — Personalised Email Sending

**Input:** Contacts with verified emails
**Output:** Same contacts with `send_status` and `message_id` populated

Before a single email fires, the pipeline **halts** and presents a full summary:

- **CLI mode:** A formatted table printed to terminal, followed by `[y/N]` prompt
- **Web dashboard:** A modal slides up with the complete send list; you click **Send All** or **Cancel**

Once confirmed, each email is sent individually via Brevo's `/v3/smtp/email` REST endpoint with personalised HTML + plain-text content. Variant copy is chosen based on seniority (C-Suite vs VP/Director). Each email is tagged `Coldmail-pipeline` for Brevo tracking.

---

## 🏗️ Project Architecture

```
                          ┌─────────────────────────────-┐
                          │         main.py              │
                          │  (Orchestrator + CLI + --ui) │
                          └──────────────┬─────────────-─┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
          ┌─────────▼─────-─┐   ┌─-────────▼──────┐   ┌───────▼────────┐
          │   pipeline/     │   │    utils/       │   │  dashboard/    │
          │                 │   │                 │   │                │
          │ stage1_ocean    │   │ logger.py       │   │ server.py      │
          │ stage2_prospeo  │   │ rate_limiter.py │   │ template.py    │
          │ stage3_enricher │   │ checkpoint.py   │   │                │
          │ stage4_brevo    │   │                 │   │  Flask + SSE   │
          └─────────────────┘   └─────────────────┘   └────────────────┘
                    │                    │
          ┌─────────▼──────-┐   ┌─────────▼──────┐
          │ email_templates │   │   data/runs/   │
          │                 │   │                │
          │ outreach.py     │   │ <run_id>/      │
          │ (copy variants) │   │  meta.json     │
          └─────────────────┘   │  stage1_*.json │
                                │  stage2_*.json │
                                │  stage3_*.json │
                                │  stage4_*.json │
                                └────────────────┘
```

### Data Flow

```
main.py
  │
  ├─► stage1_ocean.run(seed_domain, config)
  │         └─► Ocean.io API  →  [companies]
  │         └─► checkpoint.save(run_id, "stage1_companies", companies)
  │
  ├─► stage2_prospeo.run(companies, config)
  │         └─► Prospeo /search-person  →  [contacts (no email)]
  │         └─► checkpoint.save(run_id, "stage2_contacts", contacts)
  │
  ├─► stage3_enricher.run(contacts, config)
  │         └─► Eazyreach API  ──(failure?)──► Prospeo /enrich-person
  │         └─► [contacts (with verified emails)]
  │         └─► checkpoint.save(run_id, "stage3_emails", contacts)
  │
  ├─► [SAFETY CHECKPOINT — CLI prompt / Web modal]
  │
  └─► stage4_brevo.run(contacts, config)
            └─► email_templates/outreach.py  →  personalised HTML + text
            └─► Brevo /v3/smtp/email  →  sent
            └─► checkpoint.save(run_id, "stage4_sent", contacts)
```

---

## 📁 File Structure

```
coldmail-pipeline/
│
├── main.py                        # Entry point — CLI orchestrator + --ui flag
│
├── pipeline/                      # One file = one stage
│   ├── __init__.py
│   ├── stage1_ocean.py            # Stage 1: Ocean.io lookalike search
│   ├── stage2_prospeo.py          # Stage 2: Prospeo decision-maker search
│   ├── stage3_enricher.py         # Stage 3: Eazyreach (primary) + Prospeo (fallback)
│   └── stage4_brevo.py            # Stage 4: Brevo transactional email send
│
├── dashboard/                     # Web dashboard (Flask + SSE)
│   ├── __init__.py
│   ├── server.py                  # Flask routes, SSE event bus, pipeline thread runner
│   └── template.py                # Complete SPA HTML/CSS/JS (served inline, no static files)
│
├── utils/                         # Shared infrastructure
│   ├── __init__.py
│   ├── logger.py                  # Rich console logger with plain-print fallback
│   ├── rate_limiter.py            # Retry + exponential back-off (tenacity or stdlib)
│   └── checkpoint.py              # Save/load/resume pipeline state as JSON
│
├── email_templates/
│   └── outreach.py                # Personalised email copy (C-Suite + VP variants)
│
├── data/
│   └── runs/                      # Checkpoint data, auto-created at runtime
│       └── <run_id>/
│           ├── meta.json
│           ├── stage1_companies.json
│           ├── stage2_contacts.json
│           ├── stage3_emails.json
│           └── stage4_sent.json
│
├── .env.example                   # Copy → .env and fill in your keys
└── requirements.txt
```

---

## 🌐 Domain & Sender Setup — `navdev.xyz`

The assignment requires a company domain to sign up for Ocean.io (which rejects personal Gmail addresses). Here's exactly how this was set up:

### Step 1 — Register the Domain on Namecheap

A custom domain **`navdev.xyz`** was registered via [Namecheap](https://namecheap.com).

### Step 2 — Create a Work Email

Using Namecheap's free email forwarding (or Zoho Mail free tier), a professional work email was created:

```
naveenkumarm@navdev.xyz
```

This address is used as the **`SENDER_EMAIL`** in the `.env` config — the "From" address that all outreach emails are sent from via Brevo.

### Step 3 — Verify the Sender in Brevo

Before Brevo will send from your domain, it must be verified:

1. Log into [app.brevo.com](https://app.brevo.com)
2. Go to **Senders & IP** → **Add a Sender**
3. Add `naveenkumarm@navdev.xyz` and verify via the email link sent to that inbox
4. Optionally set up DKIM/SPF DNS records for better deliverability

### Step 4 — Sign Up for Ocean.io

Ocean.io requires a **company email** (non-Gmail/Yahoo/etc.) to create an account:

```
Signed up at ocean.io using:  naveenkumarm@navdev.xyz
```

> ⚠️ **Order matters:** Domain → Work email → Ocean.io signup → All other accounts. Skipping this sequence means you can't create an Ocean.io account.

### Summary

| Item | Value |
|---|---|
| Domain | `navdev.xyz` |
| Work Email | `naveenkumarm@navdev.xyz` |
| Used for | Brevo sender, Ocean.io signup |
| Cost | ~$1–2/year |

---

## 📦 Installation

### Prerequisites

- Python 3.10 or higher
- A terminal (macOS/Linux/WSL on Windows)
- API accounts for Ocean.io, Prospeo, Eazyreach, Brevo (see [Configuration](#-configuration))

### 1 — Clone the repository

```bash
git clone https://github.com/Naveen-Kumar-Murugan/coldmail-pipeline.git
cd coldmail-pipeline
```

### 2 — Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# OR
venv\Scripts\activate           # Windows
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

**Core dependencies (required):**

| Package | Version | Purpose |
|---|---|---|
| `requests` | ≥ 2.28.0 | All API HTTP calls |
| `python-dotenv` | ≥ 1.0.0 | Load `.env` config |
| `flask` | ≥ 3.0.0 | Web dashboard server |
| `rich` | ≥ 13.0.0 | Coloured terminal output, tables, progress bars |
| `tenacity` | ≥ 8.0.0 | Structured retry logic with exponential back-off |

> Without `rich` and `tenacity`, the pipeline still works fully — it gracefully falls back to plain `print()` statements and a stdlib retry loop.

---

## 🔧 Configuration

### 1 — Copy the example env file

```bash
cp .env.example .env
```

### 2 — Fill in your API keys

Open `.env` in any text editor:

```env
# ── Required API Keys ──────────────────────────────────────────
OCEAN_API_KEY=your_ocean_io_api_token
PROSPEO_API_KEY=your_prospeo_api_key
EAZYREACH_CLIENT_ID=your_eazyreach_client_id
EAZYREACH_CLIENT_SECRET=your_eazyreach_client_secret
BREVO_API_KEY=your_brevo_api_key

# ── Sender (must match a verified Brevo sender) ─────────────────
SENDER_EMAIL=naveenkumarm@navdev.xyz
SENDER_NAME=Naveen Kumar

# ── Tuning (optional) ───────────────────────────────────────────
OCEAN_LOOKALIKE_COUNT=15        # How many lookalike companies to fetch
PROSPEO_MAX_PER_COMPANY=3       # Max decision-makers per company
SKIP_SEND_CONFIRM=false         # Set true ONLY to auto-fire (dangerous!)
```

### Where to find each API key

| Key | Where to get it |
|---|---|
| `OCEAN_API_KEY` | [app.ocean.io](https://app.ocean.io) → Settings → API Tokens |
| `PROSPEO_API_KEY` | [app.prospeo.io/api](https://app.prospeo.io/api) → Your API Key |
| `EAZYREACH_API_KEY` | [eazyreach.app/dashboard](https://eazyreach.app/dashboard) → API section |
| `BREVO_API_KEY` | [app.brevo.com](https://app.brevo.com) → Settings → API Keys → Generate |

---

## ▶️ Running the Pipeline

### CLI Mode

```bash
# Basic run — 15 lookalike companies, 3 contacts per company
python main.py stripe.com

# Fetch more lookalike companies
python main.py stripe.com --count 25

# Limit contacts per company (saves API credits)
python main.py stripe.com --max-per-company 2

# Dry run — Stage 1–3 only, no emails sent
python main.py stripe.com --dry-run

# Resume an interrupted run (reads from checkpoint files)
python main.py stripe.com --resume

# List all saved runs
python main.py --list-runs

# Skip the send-confirmation prompt (auto-fires emails — use with extreme care)
python main.py stripe.com --skip-confirm
```

### Complete CLI Flags Reference

| Flag | Short | Default | Description |
|---|---|---|---|
| `domain` | — | required | Seed company domain, e.g. `stripe.com` |
| `--count` | `-c` | `15` | Number of lookalike companies to fetch |
| `--max-per-company` | `-m` | `3` | Max decision-makers per company |
| `--resume` | `-r` | `false` | Resume last interrupted run for this domain |
| `--list-runs` | — | — | Print all saved runs and exit |
| `--dry-run` | — | `false` | Run Stages 1–3 only, skip email send |
| `--skip-confirm` | — | `false` | Skip send-confirmation prompt |
| `--ui` | — | `false` | Open the web dashboard instead of CLI |
| `--port` | — | `5055` | Port for the web dashboard |

### What you'll see in the terminal

```
════════════════════════════════════════════════════════════
  🚀  Coldmail Outreach Pipeline
  Seed domain : stripe.com
  Run ID      : 20240615_143022_stripe_com
  Started     : 2024-06-15 14:30:22
════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────
  Stage 1 · Ocean.io  Finding lookalikes for stripe.com
────────────────────────────────────────────────────────────
  ·  Requesting 15 lookalike companies …
  ✓  Stage 1 complete — 14 valid lookalike companies found.

  #   Name                            Domain                    Size
  1   Braintree                       braintree.com             501-1000
  2   Adyen                           adyen.com                 1001-5000
  ...

────────────────────────────────────────────────────────────
  Stage 2 · Prospeo  Finding decision-makers
────────────────────────────────────────────────────────────
  [1/14] Searching Braintree (braintree.com) … 3 contact(s) added.
  [2/14] Searching Adyen (adyen.com) … 3 contact(s) added.
  ...
  ✓  Stage 2 complete — 38 unique contacts across 14 companies.

────────────────────────────────────────────────────────────
  Stage 3 · Email Enrichment  Resolving verified emails
────────────────────────────────────────────────────────────
  [1/38] Enriching Jane Smith @ braintree.com … → jane.smith@braintree.com
  [2/38] Enriching John Doe @ adyen.com … → not found.
  ...
  ✓  Stage 3 complete — 27 resolved, 8 not found, 3 errors.

════════════════════════════════════════════════════════════
  ⚠  READY TO SEND — 27 email(s)
════════════════════════════════════════════════════════════
  #   Name                      Email
  1   Jane Smith                jane.smith@braintree.com
  ...
════════════════════════════════════════════════════════════
  Proceed and send all emails? [y/N]: y

────────────────────────────────────────────────────────────
  Stage 4 · Brevo  Sending personalised outreach emails
────────────────────────────────────────────────────────────
  [1/27] Sending to Jane Smith <jane.smith@braintree.com> … sent ✓
  ...
  ✓  Stage 4 complete — 27 sent, 0 failed.

────────────────────────────────────────────────────────────
  Pipeline Complete
────────────────────────────────────────────────────────────
  Seed domain         : stripe.com
  Lookalike companies : 14
  Contacts found      : 38
  Emails resolved     : 27
  Emails sent         : 27
  Send failures       : 0
  Total time          : 94.3s
```

---

## 🌐 Web Dashboard

### Starting the dashboard

```bash
python main.py --ui
# Opens http://localhost:5055 automatically

python main.py --ui --port 8080
# Use a custom port
```

### Dashboard features

The single-page app communicates with the Flask backend over **Server-Sent Events (SSE)** — a persistent HTTP connection where the server pushes JSON events to the browser in real time.

```
Browser                           Flask Server
   │                                   │
   │── GET /events ─────────────────►  │
   │◄─ SSE stream (text/event-stream) ─│  (persistent, keep-alive)
   │                                   │
   │   ◄── {"type":"stage_start",...}  │  (as pipeline progresses)
   │   ◄── {"type":"log",...}          │
   │   ◄── {"type":"stage_done",...}   │
   │   ◄── {"type":"confirm_needed",...}│
   │── POST /confirm ──────────────►   │  (user clicks Send / Cancel)
   │   ◄── {"type":"email_sent",...}   │
   │   ◄── {"type":"complete",...}     │
```

**What you see live:**

| Element | Behaviour |
|---|---|
| **Stage track** | Each circle animates: idle → glowing/bouncing active → solid green done; connecting lines fill green as stages complete |
| **Metrics row** | Companies / Contacts / Emails / Sent tick up in real time |
| **Contacts table** | Rows slide in as each contact is found; email cells update from `—` to a green verified badge when Stage 3 resolves them |
| **Activity log** | Every pipeline event streams into the sidebar, colour-coded by level (green = ok, yellow = warn, red = error) |
| **Confirmation modal** | Slides up before Stage 4 with the full send list; click **Send All Emails** or **Cancel** |
| **Progress bar** | Tracks 0→25→50→75→100% across the 4 stages with a shimmer animation while active |
| **Live badge** | Green pulsing dot + "LIVE" appears while the pipeline is running |
| **Auto-reconnect** | If the SSE connection drops, the browser reconnects in 3 seconds and a state snapshot restores the full UI |

### Dashboard API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | `GET` | Serves the single-page dashboard HTML |
| `GET /state` | `GET` | Returns current pipeline state as JSON snapshot |
| `POST /run` | `POST` | Starts a new pipeline run. Body: `{"domain":"stripe.com","count":15}` |
| `POST /confirm` | `POST` | Sends the user's confirmation. Body: `{"approved":true}` |
| `GET /events` | `GET` | SSE stream — connect and receive live events |

---

## 🛡️ Error Handling & Resilience

The pipeline is built to handle real-world messiness gracefully. No single API failure crashes the run.

### Per-stage error handling

**Stage 1 — Ocean.io**

| Error | Behaviour |
|---|---|
| `HTTP 402` | Logs "Insufficient credits", raises immediately |
| `HTTP 401/403` | Logs "Authentication failed — check OCEAN_API_KEY", raises |
| `HTTP 422` | Logs "Validation error — is the domain valid?", raises |
| Junk/social domain returned | Silently filtered out (`_is_junk_domain()`) |
| Seed domain returned as a lookalike | Filtered out before passing to Stage 2 |
| Empty results | Logs warning, exits gracefully |

**Stage 2 — Prospeo Search**

| Error | Behaviour |
|---|---|
| `NO_RESULTS` for a domain | Logs "no contacts found", continues to next company |
| `INSUFFICIENT_CREDITS` | Logs error, stops Stage 2, passes whatever was collected so far to Stage 3 |
| `HTTP 401/403` | Logs "auth failed", stops Stage 2 |
| Any other HTTP error | Logs warning, skips that company, continues |
| Duplicate contact (same `person_id` or `linkedin_url`) | Deduplicated before being added to the list |

**Stage 3 — Email Enricher**

| Error | Behaviour |
|---|---|
| Eazyreach failure / `NotImplementedError` | Automatically falls back to Prospeo `/enrich-person` |
| `NO_MATCH` (Prospeo) | Sets `email_status = "NOT_FOUND"`, contact kept in dataset but skipped in Stage 4 |
| `INSUFFICIENT_CREDITS` (Prospeo) | Logs error, stops Stage 3, passes partial results to Stage 4 |
| `HTTP 401/403` | Logs auth failure, stops Stage 3 |
| Any other exception | Logs warning with contact name, sets `email_status = "EXCEPTION"`, continues |
| Credit protection | `only_verified_email: true` — you are **not charged** if no email is found |

**Stage 4 — Brevo Send**

| Error | Behaviour |
|---|---|
| `HTTP 401` | Logs "Invalid API key", stops immediately |
| `HTTP 400` (bad request) | Logs Brevo's error message, marks contact `FAILED:BAD_REQUEST`, continues |
| Any other HTTP error | Logs warning, marks contact `FAILED:HTTP_<code>`, continues to next |
| General exception | Marks contact `FAILED:EXCEPTION`, continues |
| Duplicate emails | Deduplicated on email address before the send loop begins |
| User cancels at checkpoint | All contacts marked `CANCELLED`, no emails sent |
| No emails resolved | Stage 4 is skipped entirely with a clear warning |

---

## 💾 Checkpoint System

Every stage saves its output to disk **immediately after completion**. This means if the pipeline crashes, is interrupted (`Ctrl+C`), or hits a fatal API error mid-run, you can **resume from the last completed stage** without re-spending any API credits.

### How checkpoints work

```
data/runs/
└── 20240615_143022_stripe_com/     ← Run ID = timestamp + seed domain
    ├── meta.json                   ← {"run_id": ..., "seed_domain": ..., "started_at": ...}
    ├── stage1_companies.json       ← Written after Stage 1 completes
    ├── stage2_contacts.json        ← Written after Stage 2 completes
    ├── stage3_emails.json          ← Written after Stage 3 completes
    └── stage4_sent.json            ← Written after Stage 4 completes
```

Each file is written **atomically**: written to a `.tmp` file first, then renamed. This prevents a half-written file from being read as valid data on resume.

### Resuming a run

```bash
# If your run was interrupted at Stage 3:
python main.py stripe.com --resume

# The pipeline detects checkpoints and skips completed stages:
#   ↩  Resuming stage1_companies from checkpoint (14 records)
#   ↩  Resuming stage2_contacts from checkpoint (38 records)
#   Stage 3 · Email Enrichment starts fresh from where it left off
```

### Listing all saved runs

```bash
python main.py --list-runs

#   Run ID                               Seed Domain      Companies  Contacts  Sent
#   20240615_143022_stripe_com           stripe.com       14         38        27
#   20240614_092100_shopify_com          shopify.com      12         31        0
```

---

## ⏱️ Rate Limiting & Retry Logic

Each API has its own rate limits. The pipeline respects all of them automatically.

### Per-API rate limits and sleep strategy

| API | Limit | Sleep between calls | Notes |
|---|---|---|---|
| **Ocean.io** | Not documented (generous) | None (single call) | Only called once per run |
| **Prospeo Search** | 1–2 req/s, 30–60 req/min (Starter) | `1.1s` between companies | Tracks `x-minute-request-left` header |
| **Prospeo Enrich** | 5 req/s, 300 req/min (Starter) | `0.25s` between contacts | ≈4 req/s, safely under the 5/s limit |
| **Eazyreach** | Plan-dependent | `0.25s` | Mirrors Prospeo enrich timing |
| **Brevo Send** | 1,000 req/s (free plan) | `0.3s` | Polite pause to avoid spam triggers |

### HTTP 429 handling

If any API returns `HTTP 429`, the pipeline:

1. Reads the `Retry-After` header (defaults to 5s if missing)
2. Sleeps for that duration
3. Raises `RateLimitError` — which triggers the retry decorator

### Retry decorator

Every external API call is wrapped with `@retry_request`, which provides exponential back-off for transient failures:

```python
# With tenacity installed:
@retry(
    retry=retry_if_exception_type((ConnectionError, Timeout, RateLimitError)),
    wait=wait_exponential(multiplier=1, min=2s, max=30s),
    stop=stop_after_attempt(4),
)

# Without tenacity (stdlib fallback):
# Attempt 1 → fail → sleep 2s
# Attempt 2 → fail → sleep 4s
# Attempt 3 → fail → sleep 8s
# Attempt 4 → fail → raise (propagates to stage error handler)
```

**What triggers a retry:**
- `requests.exceptions.ConnectionError` — network blip
- `requests.exceptions.Timeout` — slow API response (30s timeout on all calls)
- `requests.exceptions.ChunkedEncodingError` — broken response stream
- `RateLimitError` — HTTP 429 from any API

**What does NOT trigger a retry:**
- `HTTP 400` (bad request — your payload is wrong, retrying won't help)
- `HTTP 401/403` (authentication — retrying won't help)
- `HTTP 402` (insufficient credits — retrying won't help)
- `HTTP 404` (not found)

---

## ✉️ Email Copywriting

Email copy lives in `email_templates/outreach.py`. Two personalised variants are chosen automatically based on the contact's seniority:

### C-Suite / Founder variant
Targeted at CEOs, CTOs, COOs, Founders. Leads with strategic business value and ROI — short and punchy, assumes they get 100+ emails a day.

```
Subject: Quick question about {company}'s outreach pipeline

Hi {first_name},

I came across {company} while researching companies in your space — impressive
traction, especially on the sales side.

At Coldmail, we help growth-stage teams automate their outbound pipeline
end-to-end — from prospect discovery to personalised outreach — without
adding headcount.

For {company} specifically, I think there's a clear opportunity to 3x outbound
volume while cutting the manual work your team currently does between tools.

Worth a 15-minute call this week to see if it's a fit?
```

### VP / Director variant
Targeted at VPs and Directors. Leads with operational pain points and measurable outcomes — acknowledges they own the execution.

```
Subject: Automating {company}'s outreach — quick idea

Hi {first_name},

I noticed {company} is scaling in a market we work with closely. As {title},
you're likely balancing pipeline targets with a team that doesn't have
infinite hours.

Coldmail builds fully automated outbound pipelines: one domain in →
lookalike discovery → verified contacts → personalised emails sent —
zero manual steps.

Teams we work with typically see 40–60% more qualified meetings in the
first 30 days without adding BDRs.
```

To customise the copy, edit the template strings directly in `email_templates/outreach.py`. The `build_email(contact, sender_name)` function is the only public interface — it returns `{"subject", "html_body", "text_body"}`.

---

## 📡 API Reference Summary

### Ocean.io — Lookalike Search

```
POST https://api.ocean.io/v2/search/companies?apiToken=<key>
Headers: x-api-token: <key>
         Content-Type: application/json

Body: {
  "size": 15,
  "companiesFilters": {
    "lookalikeDomains": ["stripe.com"],
    "socialMedias": { "medias": ["linkedin"], "mode": "anyOf" }
  }
}

Response: { "companies": [...], "totalHits": 512 }
```

### Prospeo — Search Person

```
POST https://api.prospeo.io/search-person
Headers: X-KEY: <key>
         Content-Type: application/json

Body: {
  "page": 1,
  "filters": {
    "company": { "websites": { "include": ["acme.com"] } },
    "person_seniority": { "include": ["C-Suite", "VP", "Founder/Owner", "Director"] }
  }
}

Response: { "results": [{ "person": {...}, "company": {...} }], "pagination": {...} }
```

### Prospeo — Enrich Person (Stage 3 fallback)

```
POST https://api.prospeo.io/enrich-person
Headers: X-KEY: <key>
         Content-Type: application/json

Body: {
  "only_verified_email": true,
  "data": { "person_id": "aaa..." }        // or linkedin_url, or name + domain
}

Response: { "person": { "email": { "email": "...", "status": "VERIFIED" } } }
```

### Brevo — Send Transactional Email

```
POST https://api.brevo.com/v3/smtp/email
Headers: api-key: <key>
         content-type: application/json

Body: {
  "sender":      { "name": "Naveen Kumar", "email": "naveenkumarm@navdev.xyz" },
  "to":          [{ "email": "jane@acme.com", "name": "Jane Smith" }],
  "subject":     "Quick question about Acme's outreach pipeline",
  "htmlContent": "<html>...</html>",
  "textContent": "Hi Jane, ...",
  "tags":        ["Coldmail-pipeline"]
}

Response: { "messageId": "<abc@relay.brevo.com>" }
```

---

## 🧰 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Language** | Python 3.10+ | Clean syntax, great library ecosystem |
| **HTTP client** | `requests` | Simple, reliable, widely understood |
| **Config** | `python-dotenv` | `.env` file support, no secrets in code |
| **Web server** | `Flask 3.x` | Lightweight, perfect for SSE streaming |
| **Real-time** | Server-Sent Events (SSE) | One-way push from server to browser, zero WebSocket complexity |
| **Terminal UI** | `rich` (optional) | Tables, progress bars, colours with zero effort |
| **Retry logic** | `tenacity` (optional) | Declarative exponential back-off decorators |
| **Persistence** | Plain JSON files | No database dependency, human-readable, Git-committable |
| **Concurrency** | `threading.Thread` | Pipeline runs in a background thread; Flask serves the UI concurrently |

---

## 🔒 Security Notes

- API keys are stored in `.env` and loaded via `python-dotenv`. **Never commit `.env` to Git.**
- Add `.env` to `.gitignore` immediately:
  ```bash
  echo ".env" >> .gitignore
  ```
- The web dashboard listens on `127.0.0.1` (localhost only) by default. It is **not** intended to be exposed to the internet.
- The confirmation checkpoint before Stage 4 is a hard safety gate — emails cannot fire without an explicit `y` or a browser modal approval.

---

## 🤝 Built By

**Naveen Kumar M**
Work email: [mnaveenkumar.dev04@gmail.com](mailto:mnaveenkumar.dev04@gmail.com)
Portfolio: [navdev.xyz](https://naveen-kumar-m.vercel.app/)

---