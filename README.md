# AI Workshop

The Flask events API, tests, and database setup SQL are in [`backend/`](backend/).
See the [backend README](backend/README.md) for setup and API documentation.

## Render

Use the root `render.yaml` for a Blueprint deployment, or configure a Python web service with:

- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn run:app --bind 0.0.0.0:$PORT --workers 1 --timeout 60 --access-logfile - --error-logfile -`
- Health Check Path: `/health`

Set the environment variables described in the backend README in Render. Credentials and local environments are excluded from Git.
