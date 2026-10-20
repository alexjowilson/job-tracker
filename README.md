# job-tracker

A Django + PostgreSQL app for tracking a job search from posting to offer. It imports new postings from **jobscout**, my automated job-posting pipeline, and tracks every application through each stage of the process.

> **Status:** in active development. See the [roadmap](#roadmap) for what's built and what's next.

## Why

I run a daily pipeline (jobscout) that finds and scores new job postings. Before this app, tracking which ones I'd applied to, with which résumé, and where each process stood lived in scattered notes. job-tracker gives that data one home, with a real schema, and feeds back into jobscout so postings I've already applied to stop resurfacing.

## How it works

```
jobscout (daily, GitHub Actions)        job-tracker (Django)
──────────────────────────────          ─────────────────────────────
scrape job boards                        manage.py import_jobscout
  → filter + score                         → upsert Companies + Postings
  → LLM review                           Django admin
  → digest + seen.json   ───────────▶      → mark applied, update status
                                         applied list
                         ◀───────────      → jobscout skips these
```

1. **Import:** a management command reads jobscout's output and creates or updates companies and postings. Re-running it is safe; postings are matched by URL.
2. **Track:** the Django admin is the day-to-day interface: filter postings by tier or company, mark one applied, and record the résumé version, referral, status and notes.
3. **Feed back:** job-tracker exports the list of applied postings so jobscout can skip them in future digests.

jobscout lives in a separate private repo. This app only reads its output files by path; none of that data is committed here.

## Data model

| Model | Key fields |
| --- | --- |
| `Company` | name (unique), careers URL |
| `Posting` | company, title, URL (unique), location, posted date, fit score (1–10), tier, first seen |
| `Application` | posting (one-to-one), applied date, résumé version, referral, status, notes |

**Application status:** Applied → Recruiter screen → Interviewing → Offer, or Rejected / Withdrawn.

## Tech stack

- Python 3, Django
- PostgreSQL 16 (Docker Compose for local development)
- pytest + pytest-django
- GitHub Actions for CI

## Getting started

**Prerequisites:** Python 3.11+ and Docker Desktop (running).

```bash
git clone https://github.com/alexjowilson/job-tracker.git
cd job-tracker

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Configure:** copy the example settings, then fill in `DJANGO_SECRET_KEY` and `DB_PASSWORD` in `.env`.

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(50))"   # paste as DJANGO_SECRET_KEY
```

**Start PostgreSQL and the app:**

```bash
docker compose up -d          # Postgres 16; first run initializes the database
docker compose ps             # wait until the db shows "healthy"

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open http://localhost:8000/admin and log in.

**Day to day:**

| Task | Command |
| --- | --- |
| Start the database | `docker compose up -d` |
| Stop it (data is kept) | `docker compose stop` |
| View database logs | `docker compose logs db` |
| Reset everything (deletes all data) | `docker compose down -v` |

### Importing from jobscout

```bash
python manage.py import_jobscout --path ~/Developer/jobscout
```

### Running tests

```bash
pytest
```

Tests use small made-up fixtures in `tracker/tests/fixtures/`, so they run without any real job-search data.

## Roadmap

- [x] Django project and `tracker` app
- [x] PostgreSQL via Docker Compose, settings read from `.env`
- [x] `Company`, `Posting` and `Application` models
- [x] Admin with filters, search and an application inline
- [ ] `import_jobscout` management command
- [ ] Tests for the models and the import (pytest-django)
- [ ] GitHub Actions CI
- [ ] Export the applied list back to jobscout
- [ ] Pipeline view: applications by status and résumé version
- [ ] Demo deployment on AWS with seeded sample data

## Privacy

Real application data stays in my local database. The repo contains code and sample fixtures only; secrets live in `.env`, which is git-ignored.
