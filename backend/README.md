# Flask + Supabase Events API

This backend implements the five endpoints in `api.png` against the `users`,
`events`, and `registrations` tables shown in `database.png`. Authentication is
intentionally deferred. The Supabase service-role key is used only by Flask and
must never be sent to a browser or committed to source control.

Clients need no login, bearer token, or API key. The organizer-only restriction
in the image is deferred along with authentication. `user_id` identifies the
user whose registrations to create or retrieve; it is not a credential.

| Method | Endpoint | Input |
| --- | --- | --- |
| GET | `/api/events` | None |
| GET | `/api/events/{id}` | Event UUID in the path |
| POST | `/api/registrations` | JSON with `user_id` and `event_id` |
| GET | `/api/me/registrations` | `user_id` query parameter |
| GET | `/api/events/{id}/registrations` | Event UUID in the path |

`api.http` contains ready-to-run requests for a REST Client. Set its `userId` and
`eventId` variables to existing database UUIDs. Users and events must already
exist in the tables shown in your database image.

## Setup

Run the following commands from the `backend` directory (`cd backend` from the repository root).

1. Create and activate a virtual environment:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. If `.env` does not already exist, copy `.env.example` to `.env`. Set
   `SUPABASE_URL` and `SUPABASE_SECRET_KEY` from your Supabase project's API Keys
   settings. A legacy `SUPABASE_SERVICE_ROLE_KEY` is also accepted. A
   `SUPABASE_PUBLISHABLE_KEY` does not replace the server key for this backend.
   Keep the secret key on the server only. See the
   [Supabase API key guide](https://supabase.com/docs/guides/getting-started/api-keys).

4. In the Supabase SQL editor, review and run `supabase/rls.sql`. It enables RLS,
   removes direct `anon`/`authenticated` access, and grants the backend service
   role only the operations required by this API.

5. Start Flask:

   ```powershell
   python run.py
   ```

The API is available at `http://127.0.0.1:5000`.
Opening that base URL (or `/api`) displays the available endpoints. Use
`/api/events` to browse events and `/health` to check that the server is running.
After editing the backend, restart `python run.py` to load changes when debug
mode is disabled. Hosted deployments must be redeployed to load code changes.

## Deploy to Render

The repository-root `render.yaml` configures a Python web service with Gunicorn,
Render's assigned `PORT`, stdout/stderr logs, and the existing `/health` endpoint.
`.python-version` selects Python 3.13. `requirement.txt` includes
`requirements.txt`, so either filename installs the same dependencies. Gunicorn
is installed on Linux (Render); Windows development still uses `python run.py`.

1. Push this backend to a Git repository, keeping `.env` out of Git.
2. In Render, choose **New > Blueprint**, connect the repository, and select
   `render.yaml`. The configuration sets `rootDir: backend`.
3. Enter `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` when prompted. Use the
   backend service-role key, never a frontend key. Do not paste credentials into
   `render.yaml` or commit them.
4. Deploy, then visit `https://YOUR-SERVICE.onrender.com/health` and
   `https://YOUR-SERVICE.onrender.com/api/events`.

For manual **New > Web Service** setup, use:

| Setting | Value |
| --- | --- |
| Runtime | Python 3 |
| Root Directory | `backend` |
| Build command | `pip install -r requirement.txt` |
| Start command | `gunicorn run:app --bind 0.0.0.0:$PORT --workers 1 --timeout 60 --access-logfile - --error-logfile -` |
| Health check path | `/health` |

Add the same two Supabase variables in Render's Environment settings and set
`FLASK_DEBUG=false`. Set the service's **Root Directory** to `backend`. Keep both requirement files together in that directory.

`/health` checks that Flask is running; it does not check the database. A `503`
from `/api/events` means credentials are missing; a `502` means the database
request failed. Verify the project URL, server key, existing tables, and their
permissions in that case. The SQL setup in this README remains a separate step;
deployment does not apply it automatically.

Authentication is still intentionally absent. On a public Render URL, anyone
can call these routes and supply user IDs; RLS does not protect requests
made through this privileged backend. Use test data until identity checks are
implemented. Duplicate and capacity checks also remain separate from the insert,
so simultaneous requests need database constraints/transactional enforcement
before relying on them for production bookings.

Deployment configuration follows [Render's Flask guide](https://render.com/docs/deploy-flask).

## Endpoints

Replace the UUID placeholders with IDs that exist in your Supabase tables.

### Browse events

```powershell
curl.exe http://127.0.0.1:5000/api/events
```

### Event details

```powershell
curl.exe http://127.0.0.1:5000/api/events/EVENT_UUID
```

### Create a registration

Returns `201` when created and `409` if the user is already registered or the
event has reached its non-null capacity.

```powershell
curl.exe -X POST http://127.0.0.1:5000/api/registrations `
  -H "Content-Type: application/json" `
  -d '{"user_id":"USER_UUID","event_id":"EVENT_UUID"}'
```

### User registrations

Until authentication is added, the current user is supplied explicitly as a
query parameter.

```powershell
curl.exe "http://127.0.0.1:5000/api/me/registrations?user_id=USER_UUID"
```

### Event attendee list

Returns registrations with the related user's `id`, `email`, and `role`.
No organizer ID or authentication is required in this version.

```powershell
curl.exe "http://127.0.0.1:5000/api/events/EVENT_UUID/registrations"
```

All five routes are public for now, including the attendee list, as requested.

## Responses

Successful responses use `{"data": ...}`. Errors use
`{"error": "message"}` and an appropriate HTTP status. Supabase failures are
returned as `502` without leaking database details.

## Automated tests

Tests use a fake Supabase client and do not contact your live project:

```powershell
python -m unittest discover -s tests -v
```
