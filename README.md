# AI Workshop

## Gather: frontend and backend together

This repository contains the Gather frontend in `frontend/` and the Flask API in `backend/`. Both run on the same domain. The browser uses relative `/api/...` requests, so no separate backend URL or CORS setup is needed.

### Run the complete application

From this repository's root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

Open **http://127.0.0.1:5000**. Configure `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in a root `.env`, `backend/.env`, or environment variables. A legacy `SUPABASE_SERVICE_ROLE_KEY` is also accepted. Never put keys in frontend JavaScript. Choose **Set user ID** in Gather and enter an existing database user UUID.

### Deploy the complete application to Vercel

1. Import `goyalchirag-ai/ai-workshop` from GitHub.
2. Use branch `main` and **Root Directory `./`** (not `backend` or `frontend`).
3. Use the **Flask** framework preset. The committed `vercel.json` sets the build command to `python build.py`; leave install and output directory overrides unset.
4. Add `SUPABASE_URL` and `SUPABASE_SECRET_KEY` in Vercel's project environment settings for Production and any Preview environments that need database access. Alternatively use `SUPABASE_SERVICE_ROLE_KEY` instead of the secret key.
5. Deploy. Check `/` for Gather, `/health` for process health, and `/api/events` for database connectivity.

`server.py` exports the Flask `app` for Vercel. `build.py` copies browser assets into `public/` for Vercel's CDN; Flask serves the homepage and API. Python is pinned to 3.13. No Node build is required. The local proxy in `frontend/server.py` is optional and is not part of the Vercel deployment.

This is deployment-ready source, not proof that a Vercel deployment or live database verification has completed. Authentication remains deferred in the existing API, including the attendee list. Only existing backend capabilities are exposed; creation, editing, payment, and check-in are not simulated.

Vercel reference: [Deploy a Flask app](https://vercel.com/docs/frameworks/backend/flask).

### Verification

```powershell
python build.py
node frontend/tests/app.test.cjs
python -m unittest discover -s frontend/tests -v
cd backend
python -m unittest discover -s tests -v
```

Tests use fake database responses and do not create live registrations.

The Flask events API, tests, and database setup SQL are in [`backend/`](backend/).
See the [backend README](backend/README.md) for setup and API documentation.

## Render

This folder matches the root of `goyalchirag-ai/ai-workshop` on GitHub. Its
application is in lowercase `backend/`. Use this folder's `render.yaml`, not
the outer workspace's Blueprint with `rootDir: Backend`.

Use the root `render.yaml` for a Blueprint deployment, or configure a Python web service with:

- Runtime: Python
- Branch: `main`
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 1 --timeout 60 --access-logfile - --error-logfile -`
- Health Check Path: `/health`

Set the environment variables described in the backend README in Render. Credentials and local environments are excluded from Git.

Committing this file does not change a manually configured Rust service.
After the changes are pushed, create a Blueprint from this repository's
`main` branch with Blueprint Path `render.yaml`. Review the proposed Python
service before deploying. The Blueprint names the service `events-flask-backend`;
it does not automatically migrate the existing service named `ai-workshop` or
preserve its URL. Keep the existing service until the Python service is verified.

The Blueprint prompts for `SUPABASE_URL` and `SUPABASE_SECRET_KEY`. If you use a
legacy service-role key, change the Blueprint's key entry to
`SUPABASE_SERVICE_ROLE_KEY`. Never commit either key. Render supplies `PORT`.

Verify `/health` returns HTTP 200, then separately check `/api/events` to verify
database access. No schema migrations or RLS changes are required for this fix.

Blueprint field reference: https://render.com/docs/blueprint-spec
