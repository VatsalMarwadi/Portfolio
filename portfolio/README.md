# Portfolio (Django)

Personal portfolio built with Django, PostgreSQL, Cloudinary, and WhiteNoise.

## Local setup

```bash
cd portfolio
pip install -r requirements.txt
copy .env.example .env   # Windows — fill in values
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [http://127.0.0.1:8000/home/](http://127.0.0.1:8000/home/).

## Cloudinary

Set `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` in `.env`.  
Project **Preview** uploads in admin are stored on Cloudinary.

## GitHub

1. Repo root can be `Portfolio/` (parent) or `portfolio/` — keep `portfolio/.env` out of git.
2. Use `.gitignore` at the repository root.

```bash
git init
git add .
git status   # must NOT list portfolio/.env or env/
git commit -m "Initial commit"
git push -u origin main
```

---

## Deploy on Render (recommended)

Render runs Django as a **long-lived web service** with Gunicorn — a better fit than serverless hosts.

### Option A — Blueprint (`render.yaml`)

1. Push this repo to GitHub.
2. In [Render Dashboard](https://dashboard.render.com/) → **New** → **Blueprint**.
3. Connect the repo. Set **Root Directory** to `portfolio` if the repo root is the parent folder.
4. Render creates:
   - **Web service** (`portfolio-web`)
   - **PostgreSQL** (`portfolio-db`)
5. In the web service → **Environment**, add (not in `render.yaml` secrets):

| Variable | Value |
|----------|--------|
| `CLOUDINARY_CLOUD_NAME` | from Cloudinary dashboard |
| `CLOUDINARY_API_KEY` | from Cloudinary |
| `CLOUDINARY_API_SECRET` | from Cloudinary |
| `EMAIL_HOST_USER` | Gmail address |
| `EMAIL_HOST_PASSWORD` | Gmail app password |
| `CONTACT_ADMIN_EMAIL` | your inbox |
| `DEFAULT_FROM_EMAIL` | same as Gmail |

`SECRET_KEY` and `DATABASE_URL` can be auto-generated/linked by the blueprint.

### Option B — Manual web service

1. **New** → **Web Service** → connect GitHub repo.
2. **Root Directory:** `portfolio`
3. **Runtime:** Python 3
4. **Build Command:** `./build.sh`
5. **Start Command:**
   ```bash
   gunicorn portfolio.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 2 --timeout 120
   ```
6. **New** → **PostgreSQL**, then link `DATABASE_URL` to the web service.
7. Environment variables:

| Variable | Required |
|----------|----------|
| `SECRET_KEY` | Yes |
| `DJANGO_DEBUG` | `false` |
| `DATABASE_URL` | Yes (from Render Postgres) |
| `DATABASE_SSL_REQUIRE` | `true` |
| `CLOUDINARY_*` | Yes (for project images) |
| `EMAIL_*` | Yes (for contact form) |

Render sets `RENDER_EXTERNAL_HOSTNAME` and `RENDER_EXTERNAL_URL` automatically — `settings.py` uses them for `ALLOWED_HOSTS` / CSRF.

### After first deploy

1. Open `https://YOUR-SERVICE.onrender.com/admin/`
2. Create a superuser (from your machine against production DB):
   ```bash
   set DATABASE_URL=postgres://...
   python manage.py createsuperuser
   ```
3. Add skills, projects, education, and links in admin.

### Health check

Render uses `GET /home/` (see `healthCheckPath` in `render.yaml`).

---

## Build details

- **`build.sh`** — installs deps, `collectstatic`, `migrate`
- **`gunicorn`** — production WSGI server
- **`whitenoise`** — serves static files
- **Cloudinary** — media (no persistent disk on Render)

## Notes

- Free Render services **spin down** after inactivity (slow first load).
- Contact form needs valid SMTP env vars.
- Do not commit `portfolio/.env`.
