# Gather frontend

Responsive frontend based on the supplied Gather designs and Obsidian Luminescence design system. Uses plain HTML, CSS, and JavaScript; no npm install or build step is needed. Original design files remain in `design/`.

## Run locally

The recommended integrated setup is `python server.py` from the repository root. It serves this frontend and the API together at http://127.0.0.1:5000. See the [repository README](../README.md) for Vercel deployment. The two-server instructions below are optional for separate frontend development; in this repository the backend folder is lowercase `backend`.

Start the existing backend in one PowerShell terminal:

```powershell
cd Backend
.\venv\Scripts\python.exe run.py
```

In another terminal, from the workspace root:

```powershell
python frontend/server.py
```

Open **http://127.0.0.1:3000**. The frontend server proxies `/api/` to Flask at `http://127.0.0.1:5000`, avoiding cross-origin configuration and keeping Supabase credentials on the backend.

To connect to an already deployed backend:

```powershell
python frontend/server.py --backend https://YOUR-SERVICE.onrender.com
```

Use `--port 3001` if port 3000 is occupied. The Python server is for local development. For production, serve `index.html`, `app.js`, and `styles.css` through a web server that forwards `/api/*` to your Flask service. Do not expose the design folder or server source. Hash routing needs no HTML fallback configuration.

## Features and API mapping

| Screen/action | Backend endpoint |
| --- | --- |
| Browse, search, and filter events | `GET /api/events` |
| Event details | `GET /api/events/{id}` |
| Reserve a place | `POST /api/registrations` with `user_id` and `event_id` |
| My registrations | `GET /api/me/registrations?user_id=...` |
| Organizer attendee list and CSV export | `GET /api/events/{id}/registrations` |

Choose **Set user ID** and paste the UUID of an existing database user. It is kept in session storage and is not an authentication credential. The organizer view initially shows all events; choose **My hosted events** to filter by the selected user's `organizer_id`. Attendee data is loaded only when opening an event's guest list. Refresh buttons retrieve current data; this app does not claim live subscriptions.

The UI handles API failures, missing events, empty lists, pending submissions, successful registrations, and the backend's duplicate/full-event 409 responses. Search and filtering happen locally on fetched data. CSV exports include all attendees of the selected event and neutralize spreadsheet formula prefixes.

Only fields provided by the backend are displayed. Dates on registration cards are **registration dates**, not event dates. Capacity is total capacity, not remaining availability, except in attendee view where remaining places are derived from the retrieved attendee count. Unlimited capacity is supported. The backend currently does not enforce event status on registration; the UI submits requests to it without inventing status rules.

Event creation/editing, payment, QR tickets, cancellation, event dates, locations, and check-in are not implemented because the current backend has no supporting fields or endpoints. No user names, event schedules, or registrations are fabricated. Authentication remains deferred as in the backend.

## Checks

```powershell
node --check frontend/app.js
node frontend/tests/app.test.cjs
python -m unittest discover -s frontend/tests -v
```

The proxy tests use a local fake backend and never write to Supabase.
