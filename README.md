# PEFA GraceWorks Community Services — Website & Community Data System

*Empowered by Faith, Serving with Grace*

A production-ready website for PEFA GraceWorks Community Services (PGCS), Kolwa Central Ward, Kisumu East.
It reproduces everything on the Octopizzo Foundation reference site and adds the tools a CBO needs to run
its programs, handle data responsibly and report to donors.

**Stack:** Python 3.12 · Django 5.2 · PostgreSQL 16 · Bootstrap 5.3 · vanilla JavaScript · Swiper · GLightbox ·
FullCalendar · Chart.js · Django REST Framework · TinyMCE · M-Pesa Daraja · Gunicorn · Nginx · Docker

---

## Contents

1. [What's included (and how it maps to the reference site)](#1-whats-included)
2. [Install the tools](#2-install-the-tools)
3. [Open the project in VS Code](#3-open-the-project-in-vs-code)
4. [Create the virtual environment](#4-create-the-virtual-environment)
5. [Create the PostgreSQL database](#5-create-the-postgresql-database)
6. [Configure the `.env` file](#6-configure-the-env-file)
7. [Build the database tables](#7-build-the-database-tables)
8. [Load the PGCS content and create your admin login](#8-load-content-and-create-an-admin)
9. [Run the site](#9-run-the-site)
10. [Manage content in the admin (your "WordPress dashboard")](#10-manage-content)
11. [Turn on M-Pesa donations](#11-turn-on-m-pesa)
12. [Run the automated tests](#12-run-the-tests)
13. [Deploy to production](#13-deploy-to-production)
14. [How the data is handled](#14-how-the-data-is-handled)
15. [Project structure](#15-project-structure)
16. [Customising](#16-customising)
17. [Troubleshooting](#17-troubleshooting)
18. [Still needed from the organisation](#18-still-needed-from-the-organisation)

---

## 1. What's included

### Reference site → PGCS equivalent

| Octopizzo Foundation (WordPress) | PGCS (Django) |
|---|---|
| Slider Revolution hero slider | Swiper fade slider, slides managed in admin (`HeroSlide`) |
| "The OF Vision" block | Vision & mission block from the profile |
| "Our Social Impact" menu + pages | 5 Focus Areas with goal, activities, outcomes, service standard |
| "Driving Change" WPBakery image carousel | Swiper carousel fed from the newest gallery album |
| "Clean Energy, Clean Water…" feature | Featured project with **live funding progress bar** |
| Kenya Food Bank (help-seekers + donations) | **Request Help** system with transparent vulnerability scoring + **Donate** with M-Pesa STK push |
| "About Octopizzo" | "Rooted in the PEFA Church" block |
| Programs / Future Projects | Projects (clinic, resource centre, 300 learners, WASH, vocational) with updates |
| Umechukua campaign | Any project can be a campaign: `?project=slug` donation links |
| Gallery & Blog | Albums with lightbox + YouTube, blog with categories, sharing, reading time |
| The Events Calendar plugin (`tec-api`) | Events list, **calendar view**, registration with capacity, `.ics` "add to calendar" |
| Partners strip | Partners by category (faith, government, development, community) |
| Volunteer Your Skills | Volunteer application with focus areas and status workflow |
| Contact Us | Contact form + map + WhatsApp button |
| Make a Donation | M-Pesa STK push, bank pledge, in-kind pledge, auto receipts |
| Social links | All social links editable in Site Settings |

### Added for PGCS

- **Service charter** page and **feedback/complaints tracker** with the 48-hour / 14-working-day promise built in (deadlines, overdue flags, public tracking by reference).
- **Beneficiary registry** (learners, girls, support value) that feeds live impact numbers.
- **M&E indicators** (baseline, target 2028, measurements) shown on Impact and How We Work.
- **Staff dashboard** with KPIs, 7 charts, priority queue, overdue complaints and CSV exports.
- **Governance** page with a data-driven organogram, board and management team.
- **REST API** (`/api/v1/`) for a future mobile app or partner reporting.
- SEO (sitemap, robots, Open Graph, schema.org NGO), dark mode, accessibility, image auto-compression, spam protection (honeypot + rate limits), Kenya Data Protection Act privacy notice.

---

## 2. Install the tools

Install these once. Windows instructions first; macOS/Linux notes after.

| Tool | Why | Get it |
|---|---|---|
| **Python 3.12** | Runs Django | python.org/downloads. On Windows tick **"Add python.exe to PATH"** during install. |
| **PostgreSQL 16** | Production database | postgresql.org/download. Remember the password you set for the `postgres` user. pgAdmin installs with it. |
| **Git** | Version control | git-scm.com |
| **VS Code** | Editor | code.visualstudio.com |
| **Docker Desktop** *(optional)* | Production-style stack locally | docker.com |
| **ngrok** *(for M-Pesa testing)* | Public URL for the M-Pesa callback | ngrok.com |

Check in a new terminal:

```bash
python --version      # Python 3.12.x   (macOS/Linux: python3 --version)
psql --version        # psql (PostgreSQL) 16.x
git --version
```

> **Windows:** if `psql` isn't found, add `C:\Program Files\PostgreSQL\16\bin` to your PATH (Start → "Edit the system environment variables" → Environment Variables → Path → New), then reopen the terminal.
>
> **macOS:** `brew install python@3.12 postgresql@16 && brew services start postgresql@16`
>
> **Ubuntu:** `sudo apt install python3.12 python3.12-venv postgresql postgresql-contrib libpq-dev`

---

## 3. Open the project in VS Code

1. Unzip `pgcs-website.zip` somewhere simple, e.g. `C:\Projects\pgcs-website` or `~/projects/pgcs-website`.
2. VS Code → **File → Open Folder…** → choose `pgcs-website`.
3. VS Code will offer to install the **recommended extensions** (Python, Debugger, Black, Django, PostgreSQL, Docker). Click **Install All**.
4. Open the terminal: **View → Terminal** (or <kbd>Ctrl</kbd>+<kbd>`</kbd>).
5. Start Git tracking:
   ```bash
   git init
   git add .
   git commit -m "Initial PGCS website"
   ```

---

## 4. Create the virtual environment

A virtual environment keeps this project's packages separate from everything else.

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
If PowerShell blocks the script, run once: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then activate again.

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt now starts with `(.venv)`. Then:

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

In VS Code press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> → **Python: Select Interpreter** → pick the one inside `.venv`.

---

## 5. Create the PostgreSQL database

Open **SQL Shell (psql)** on Windows (Start menu) or run `psql -U postgres` (macOS/Linux: `sudo -u postgres psql`), then:

```sql
CREATE DATABASE pgcs_db;
CREATE USER pgcs_user WITH PASSWORD 'pgcs_password';
ALTER ROLE pgcs_user SET client_encoding TO 'utf8';
ALTER ROLE pgcs_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE pgcs_user SET timezone TO 'Africa/Nairobi';
GRANT ALL PRIVILEGES ON DATABASE pgcs_db TO pgcs_user;
\c pgcs_db
GRANT ALL ON SCHEMA public TO pgcs_user;
\q
```

Use a stronger password than `pgcs_password` for anything beyond your laptop.

> Prefer clicking? In **pgAdmin**: right-click *Login/Group Roles* → Create → name `pgcs_user`, set a password, tick *Can login*. Then right-click *Databases* → Create → `pgcs_db`, owner `pgcs_user`.

> **No Postgres yet?** Leave `DATABASE_URL` out of `.env` and the site falls back to SQLite so you can look around. Switch to Postgres before going live.

---

## 6. Configure the `.env` file

```bash
# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

Open `.env` and set at least:

```ini
DEBUG=True
SECRET_KEY=<paste a random value>
DATABASE_URL=postgres://pgcs_user:pgcs_password@localhost:5432/pgcs_db
```

Generate a secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

`.env` is in `.gitignore`. Never commit it.

---

## 7. Build the database tables

```bash
python manage.py makemigrations core programs news events donations community
python manage.py migrate
```

You should see a list of `Applying … OK` lines. Re-run `makemigrations` + `migrate` whenever you change a `models.py`.

---

## 8. Load content and create an admin

Load everything from the PGCS organisation profile (about, legal status, vision, mission, 6 core values,
5 focus areas with goals/activities/outcomes, service charter, 5 projects, implementation model,
board & management roles, partners, milestones, M&E indicators, FAQs and hero slides):

```bash
python manage.py seed_pgcs --demo
```

`--demo` also adds three sample events and a first blog post so the pages aren't empty. The command is safe to run again.

Create your admin login:

```bash
python manage.py createsuperuser
```

---

## 9. Run the site

```bash
python manage.py runserver
```

Or press <kbd>F5</kbd> in VS Code and choose **Django: runserver** (uses `.vscode/launch.json`, with breakpoints).
VS Code tasks are also set up: <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> → **Tasks: Run Task**.

| URL | What it is |
|---|---|
| http://127.0.0.1:8000/ | Home page |
| /about/ · /governance/ · /service-charter/ · /partners/ · /impact/ | Who we are |
| /focus-areas/ · /focus-areas/education/ … | Focus areas |
| /projects/ · /how-we-work/ | Our work |
| /events/ · /events/calendar/ | Events |
| /blog/ · /gallery/ | Media |
| /donate/ | Donations |
| /request-help/ · /request-help/track/ | Help requests |
| /feedback/ · /feedback/track/ | Service charter feedback |
| /volunteer/ · /partner-with-us/ · /contact/ | Get involved |
| /admin/ | Content management |
| /dashboard/ | Staff data dashboard (staff only) |
| /api/v1/ | REST API |

While `EMAIL_BACKEND` is the console backend, emails (receipts, notifications) print in the terminal.

### Open the site on your phone or another laptop

Phones can't reach `127.0.0.1` on your laptop, so serve on the Wi-Fi address instead:

```bash
python manage.py runserver 0.0.0.0:8001
```

Find the laptop's address with `ipconfig` (Windows, *Wireless LAN → IPv4 Address*) or `ipconfig getifaddr en0` (macOS),
then open `http://<that address>:8001` on any phone on the **same Wi-Fi**. With `DEBUG=True` the laptop's own
addresses are allowed automatically.

**Windows:** the firewall blocks phones until you allow the port. In PowerShell **as Administrator**:

```powershell
New-NetFirewallRule -DisplayName "PGCS dev server" -Direction Inbound -Protocol TCP -LocalPort 8001 -Action Allow -Profile Private
```

and set your home Wi-Fi to *Private* (Settings → Network & internet → Wi-Fi → your network → *Private network*).

### Photos and videos

The WhatsApp photos and videos are **not in Git** (they show inmates and children; see `.gitignore`).
Copy them into `static/img/`, then load them into the gallery, hero slides, focus areas and projects:

```bash
python manage.py import_whatsapp_media            # add --ffmpeg C:/path/ffmpeg.exe to compress videos and make posters
```

Tick **Consent confirmed** on each photo in the admin once permission is on file.

---

## 10. Manage content

Everything is edited at **/admin/** — no code needed.

| To do this | Go to |
|---|---|
| Change phone, email, Paybill, bank details, socials, map, vision/mission | **Website & Organisation → Site settings** |
| Add hero slider photos | **Hero slides** (landscape, ≥1600 px wide) |
| Add board/management names and photos | **People (board & team)** |
| Edit a focus area, its activities, outcomes and charter row | **Programs & M&E → Focus areas** |
| Set a project's funding goal, cash already raised, post updates | **Projects** |
| Record M&E results | **Indicators** → add a measurement row |
| Write a story | **Blog & Gallery → Posts** (rich-text editor) |
| Upload photos | **Albums** → add photos inline (tick consent) |
| Create an event | **Events** (tick *Registration open* to take sign-ups) |
| Review help requests by priority | **Community Desk → Help requests** (filter *priority: High*) |
| Turn assisted requests into beneficiary records | Select requests → action **Register selected as beneficiaries** |
| Answer complaints | **Feedback & complaints** (the *Service charter* column shows deadlines) |
| Confirm bank / cash gifts | **Donations** → select → **Mark selected as completed** |
| Export anything to Excel | Select rows → **Export selected to CSV**, or use the dashboard |

**Staff accounts:** create users in **Authentication → Users**, tick *Staff status*, and give them only the permissions they need (e.g. a communications volunteer gets Blog & Gallery only; the Program Coordinator gets Community Desk). Use **Groups** to manage this.

Uploaded photos are automatically resized to 1920 px and compressed, so staff can upload straight from a phone.

---

## 11. Turn on M-Pesa

The donate page sends an **STK push** (PIN prompt) to the donor's phone and confirms the payment automatically.

1. Register at **developer.safaricom.co.ke** → *My Apps* → create an app with **M-Pesa Express (Lipa na M-Pesa Online)**. Copy the **Consumer Key** and **Consumer Secret**.
2. Sandbox values: shortcode `174379`; the passkey is shown on the Daraja *M-Pesa Express* simulator page.
3. Daraja must reach your callback URL over HTTPS. Locally, run in a second terminal:
   ```bash
   ngrok http 8000
   ```
   Copy the `https://….ngrok-free.app` address.
4. In `.env`:
   ```ini
   MPESA_ENV=sandbox
   MPESA_CONSUMER_KEY=...
   MPESA_CONSUMER_SECRET=...
   MPESA_SHORTCODE=174379
   MPESA_PASSKEY=...
   MPESA_CALLBACK_URL=https://YOUR-ID.ngrok-free.app/donate/mpesa/callback/
   ALLOWED_HOSTS=localhost,127.0.0.1,YOUR-ID.ngrok-free.app
   CSRF_TRUSTED_ORIGINS=http://localhost:8000,https://YOUR-ID.ngrok-free.app
   ```
5. Restart `runserver`, open `/donate/`, give KES 10 with a Safaricom test number. The status page polls and flips to **Thank you** when the callback arrives. If a callback is missed, the page asks Safaricom directly (STK query) after 25 seconds.

**Going live:** apply for **Go-Live** on the Daraja portal with the organisation's Paybill/Till (requires the registration certificate and KRA PIN). Then set `MPESA_ENV=production`, the live shortcode and passkey, and your real domain in `MPESA_CALLBACK_URL`. For a Till number use `MPESA_TRANSACTION_TYPE=CustomerBuyGoodsOnline`.

Until M-Pesa keys are set, the form still works: it records a pledge and shows the Paybill/bank details from Site Settings.

### Card and PayPal gifts

Donors can pay by **Visa, Mastercard, Amex** (no PayPal account needed) or with **PayPal**, through PayPal Checkout.

1. Sign in at **developer.paypal.com** → *Apps & Credentials* → create an app (start in **Sandbox**).
2. In `.env`:
   ```ini
   PAYPAL_ENV=sandbox
   PAYPAL_CLIENT_ID=...
   PAYPAL_CLIENT_SECRET=...
   PAYPAL_KES_PER_USD=129
   ```
3. Give on `/donate/` with a sandbox buyer account or PayPal's test card numbers. Switch to `PAYPAL_ENV=live` and live keys when ready.

PayPal does not settle in Kenyan shillings, so card and PayPal gifts are charged in **USD** and converted at
`PAYPAL_KES_PER_USD` for project totals (staff can correct a gift's *Amount in KES* in the admin).
Until keys are set, the payment step offers M-Pesa or bank transfer instead.

---

## 12. Run the tests

```bash
python manage.py test apps
```

Tests cover: every public page renders, content seeding, help-request scoring and fairness rule, honeypot spam blocking, reference tracking, service-charter deadlines and working days, the full M-Pesa flow (mocked), bank pledges, dashboard access and CSV export. Run them before every deployment.

---

## 13. Deploy to production

### Option 0 — Render (free, quickest way to share a review link)

The repo includes `render.yaml` (a Render *Blueprint*) and `build.sh`. Render's free disk is wiped on every
deploy, so uploaded photos and videos are stored on **Cloudinary** (free, no card needed).

1. **Cloudinary:** sign up at cloudinary.com → *Dashboard* → copy the **API environment variable**
   (`cloudinary://<key>:<secret>@<cloud-name>`).
2. **Render:** sign up at render.com with GitHub → **New → Blueprint** → choose this repository → **Apply**.
   When asked, fill in `CLOUDINARY_URL`, `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` and
   `DJANGO_SUPERUSER_PASSWORD` (leave the PayPal keys blank until you have them).
3. Wait for the first deploy (5–10 minutes). It creates the tables, loads the organisation profile and sample
   events, and creates your admin login. Your link is shown at the top: `https://pefa-graceworks.onrender.com`
   (or similar).
4. **Photos and videos** (they are not in Git): on your laptop, copy the database's **External Database URL**
   from Render (*pgcs-db → Connect*), then in PowerShell from the project folder:
   ```powershell
   pip install -r requirements-dev.txt
   $env:DATABASE_URL = "<External Database URL>"
   $env:CLOUDINARY_URL = "<your Cloudinary URL>"
   python manage.py import_whatsapp_media
   Remove-Item Env:DATABASE_URL, Env:CLOUDINARY_URL
   ```
   This uploads the media to Cloudinary and records it in the Render database. Refresh the site.

Every `git push` to `main` redeploys automatically. Free-plan limits: the site sleeps after 15 minutes without
visitors (the next visit takes about a minute to wake it), and the free database expires after 30 days, so
upgrade both to a paid plan before going live.

### Option A — Docker on a VPS (recommended)

Any Ubuntu 22.04/24.04 VPS with 1–2 GB RAM is enough (e.g. a Kenyan host, DigitalOcean, Hetzner, Linode).

```bash
# on the server
sudo apt update && sudo apt install -y docker.io docker-compose-v2 git
git clone <your-repo-url> pgcs && cd pgcs
cp .env.example .env && nano .env
```

Production `.env`:
```ini
DEBUG=False
SECRET_KEY=<new long random value>
ALLOWED_HOSTS=pefagraceworks.org,www.pefagraceworks.org
CSRF_TRUSTED_ORIGINS=https://pefagraceworks.org,https://www.pefagraceworks.org
ADMIN_URL=pgcs-manage/            # a less guessable admin address
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=...  EMAIL_HOST_USER=...  EMAIL_HOST_PASSWORD=...
STAFF_NOTIFICATION_EMAILS=info@pefagraceworks.org
MPESA_ENV=production
...
```
Also set `POSTGRES_PASSWORD=<strong password>` in `.env` (docker-compose reads it).

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_pgcs
docker compose exec web python manage.py createsuperuser
```

**Commit your migrations first:** run `makemigrations` on your laptop (step 7), commit the generated `apps/*/migrations/*.py` files, then deploy. The server only runs `migrate`.

**HTTPS (free, Let's Encrypt):** point your domain's A record to the server IP, then the simplest route is to install Nginx + Certbot on the host and proxy to the container:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
# change docker-compose nginx port to "8080:80", then:
sudo nano /etc/nginx/sites-available/pgcs
#   server { server_name pefagraceworks.org www.pefagraceworks.org;
#            client_max_body_size 12M;
#            location / { proxy_pass http://127.0.0.1:8080; proxy_set_header Host $host;
#                         proxy_set_header X-Forwarded-Proto $scheme;
#                         proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; } }
sudo ln -s /etc/nginx/sites-available/pgcs /etc/nginx/sites-enabled/
sudo certbot --nginx -d pefagraceworks.org -d www.pefagraceworks.org
```

**Updating the live site:**
```bash
git pull && docker compose up -d --build && docker compose exec web python manage.py migrate
```

### Option B — without Docker (Gunicorn + Nginx + systemd)

1. Install Python 3.12, PostgreSQL, Nginx; create the DB as in step 5.
2. `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
3. `python manage.py migrate && python manage.py collectstatic --noinput`
4. Create `/etc/systemd/system/pgcs.service`:
   ```ini
   [Unit]
   Description=PGCS Django
   After=network.target
   [Service]
   User=www-data
   WorkingDirectory=/srv/pgcs
   ExecStart=/srv/pgcs/.venv/bin/gunicorn config.wsgi:application -c gunicorn.conf.py
   Restart=always
   [Install]
   WantedBy=multi-user.target
   ```
   `sudo systemctl enable --now pgcs`
5. Nginx: proxy to `127.0.0.1:8000`, serve `/media/` from `/srv/pgcs/media/`, then Certbot as above. Static files are served by WhiteNoise.

### Domain

`.org` from any registrar, or `.or.ke` through a KENIC-accredited registrar (requires the registration certificate) — a strong trust signal for a Kenyan CBO.

### Backups (do this on day one)

```bash
# daily database backup at 2am, keep 30 days  (crontab -e)
0 2 * * * docker compose -f /home/USER/pgcs/docker-compose.yml exec -T db pg_dump -U pgcs_user pgcs_db | gzip > /home/USER/backups/pgcs-$(date +\%F).sql.gz && find /home/USER/backups -mtime +30 -delete
```
Also back up the `media` volume weekly, and copy backups off the server (e.g. to Google Drive with `rclone`).

Restore: `gunzip -c backup.sql.gz | docker compose exec -T db psql -U pgcs_user pgcs_db`

### Go-live checklist

- [ ] `DEBUG=False`, new `SECRET_KEY`, custom `ADMIN_URL`
- [ ] HTTPS working; `python manage.py check --deploy` shows no serious warnings
- [ ] Real email sending tested (contact form arrives)
- [ ] M-Pesa live keys tested with a real KES 10 gift
- [ ] Site Settings complete (email, Paybill, bank, socials, map)
- [ ] Demo events/post deleted or replaced; real photos uploaded with consent
- [ ] Daily backups running and a restore tested once
- [ ] Staff accounts created with least-privilege groups

---

## 14. How the data is handled

**One database, one source of truth.** Public forms write to PostgreSQL; staff work in the admin; the public impact numbers, project progress bars and dashboard are all calculated from the same tables, so the website never contradicts the records.

| Data | Where it comes from | What uses it |
|---|---|---|
| Donations | Donate form, M-Pesa callback, staff entries | Project progress, donor receipts, dashboard, CSV |
| Help requests | Request Help form | Priority queue, tracking page, beneficiary registry |
| Beneficiaries | Admin (or converted help requests) | Live counters (learners, girls), dashboard, donor reports |
| Indicators + measurements | M&E team in admin | Impact page, focus-area pages, dashboard |
| Feedback | Feedback form | SLA deadlines, overdue alerts, charter compliance % |
| Volunteers, partners, subscribers, registrations | Public forms | Admin workflows, CSV export |

**Fair prioritisation (help requests).** `HelpRequest.compute_priority()` in `apps/community/models.py` gives a 0–100 score from income band, urgency, household size, children, single parent, disability, elderly-headed and child-headed households. Households assisted in the last six months lose 15 points so support is spread across more families. The rules are written in plain Python so the committee can review and change the weights.

**Service charter, enforced by the system.** Each feedback item gets `acknowledge_by` (now + 48 h) and `resolve_by` (+14 working days, skipping weekends and fixed Kenyan public holidays). The admin and dashboard flag overdue items and calculate the percentage resolved on time.

**Integrity.** Requests run inside database transactions (`ATOMIC_REQUESTS`). M-Pesa callbacks lock the donation row (`select_for_update`) so a payment can't be counted twice, compare the paid amount with the requested amount, and keep the raw callback for audit. Every record has `created_at`/`updated_at`. Reference codes (DN-, HR-, FB-) avoid confusable characters like 0/O and 1/I.

**Performance.** Dashboard numbers use database aggregation (`Sum`, `Count`, `TruncMonth`), list pages use `select_related`/`prefetch_related`, frequently used values (site settings, menu, counters) are cached and cleared automatically by signals when data changes, and images are compressed on upload.

**Privacy and security (Kenya Data Protection Act, 2019).** Help requests require explicit consent; tracking needs both the reference **and** the phone number; the privacy notice is at `/privacy/`; staff access is controlled by Django permissions; spam is blocked by a hidden honeypot field and per-IP rate limits; production enables HTTPS-only cookies, HSTS and other security headers. PGCS processes sensitive data about vulnerable people, so register with the **Office of the Data Protection Commissioner (ODPC)** as a data controller and keep the admin URL private.

**Getting data out.** Every list in the admin can be exported to CSV (UTF-8 with BOM so Excel shows names correctly), and the dashboard has one-click exports for donations, beneficiaries, help requests, feedback, volunteers, subscribers and event registrations.

---

## 15. Project structure

```
pgcs-website/
├── config/                 settings.py (reads .env), urls.py, wsgi/asgi
├── apps/
│   ├── core/               site settings, slides, values, people, partners, milestones, counters, FAQs,
│   │   │                   home/about/governance/charter/impact pages, search, sitemap, utilities
│   │   └── management/commands/seed_pgcs.py   ← all profile content
│   ├── programs/           focus areas, projects, updates, implementation stages, M&E indicators
│   ├── news/               blog posts, categories, albums, photos, videos
│   ├── events/             events, registrations, calendar feed, .ics
│   ├── donations/          donations, M-Pesa Daraja client (mpesa.py), callback
│   ├── community/          contact, volunteers, partners, newsletter, feedback, help requests, beneficiaries
│   ├── dashboard/          staff KPIs, charts, CSV exports
│   └── api/                REST API (read-only)
├── templates/              Bootstrap 5 templates (base, partials, one folder per app)
├── static/
│   ├── css/main.css        brand system (colours from the logo, Lexend + Source Serif 4)
│   ├── js/main.js          slider, counters, donation flow, M-Pesa polling, newsletter, dark mode
│   └── img/                logo, logo mark, favicon, organogram, implementation model
├── media/                  uploads (not in Git)
├── Dockerfile · docker-compose.yml · nginx/ · gunicorn.conf.py
├── requirements.txt · requirements-dev.txt · .env.example
└── .vscode/                interpreter, formatter, debugger, tasks, recommended extensions
```

---

## 16. Customising

- **Colours & fonts:** the variables at the top of `static/css/main.css` (`--pg-navy`, `--pg-lake`, `--pg-grace`…). They are taken from the logo; the gold is reserved for giving actions.
- **Menu:** `templates/partials/_navbar.html`. Focus areas in the menu update automatically from the database.
- **A new simple page:** add a view in `apps/core/views.py`, a path in `apps/core/urls.py`, and a template extending `base.html` that includes `partials/_page_header.html`.
- **Card payments:** add Paystack or Pesapal (both support Kenyan cards and M-Pesa) as a new `method` in `Donation.METHOD_CHOICES` and a client module like `donations/mpesa.py`.
- **SMS confirmations:** Africa's Talking works well; call it next to `notify_person(...)` in the views.
- **Swahili/Dholuo:** Django's i18n is enabled (`USE_I18N=True`); wrap text in `{% translate %}` and add `LANGUAGES` in settings.

---

## 17. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'django'` | Virtual env isn't active. Run the activate command from step 4 and select the `.venv` interpreter in VS Code. |
| `password authentication failed for user "pgcs_user"` | Password in `DATABASE_URL` doesn't match step 5. Special characters in the password must be URL-encoded (`@` → `%40`). |
| `permission denied for schema public` | Run `GRANT ALL ON SCHEMA public TO pgcs_user;` inside `pgcs_db` (step 5). |
| `relation "core_sitesettings" does not exist` | Run step 7 (`makemigrations` then `migrate`). |
| CSS missing with `DEBUG=False` locally | Run `python manage.py collectstatic`. WhiteNoise serves files from `staticfiles/`. |
| Uploaded images don't show in production | Nginx must serve `/media/` (see `nginx/default.conf`). |
| CSRF verification failed on a form | Add your exact domain (with `https://`) to `CSRF_TRUSTED_ORIGINS`. |
| M-Pesa: "Invalid Access Token" | Wrong consumer key/secret, or production keys used with `MPESA_ENV=sandbox`. |
| M-Pesa prompt arrives but page never confirms | Callback URL unreachable: check ngrok is running and `MPESA_CALLBACK_URL` ends in `/donate/mpesa/callback/`. The page will still confirm via STK query after ~25 s. |
| PowerShell won't activate venv | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |

---

## 18. Still needed from the organisation

These are marked "[Insert …]" in the profile. Add them in **Site settings** and **People**:

- Official email address (e.g. `info@pefagraceworks.org`) and domain
- P.O. Box
- M-Pesa Paybill/Till and bank account details
- Names and photos of the Executive Board and Management Team
- Social media links and the Google Maps embed for the PEFA Church compound
- Photos for the hero slider, focus areas, projects and gallery (with consent)
- Funding goals (KES) for the Community Health Clinic and Resource Centre

*Together, we build thriving, holistic communities.*
