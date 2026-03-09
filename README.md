# Gingerly — Email Notification Platform

A full-stack email notification system built with Flask (REST API) and Next.js (frontend).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9+, Flask 3.0 |
| Database | SQLite via SQLAlchemy ORM |
| Auth | JWT (Flask-JWT-Extended), bcrypt password hashing |
| Email | Flask-Mail over SMTP (Gmail / SendGrid) |
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| HTTP Client | Axios |

---

## Database

The app uses **SQLite** — a single file (`backend/gingerly.db`) created automatically on first run. No database server is required.

SQLAlchemy manages the schema. Tables are created via `db.create_all()` inside the app factory, so there are no migration files to run.

| Table | Purpose |
|-------|---------|
| `users` | Accounts with role, plan, and superuser flag |
| `contacts` | Address book entries per user |
| `emails` | Individual sent email records with delivery status |
| `groups` | Contact groups (gold plan users only) |
| `group_contacts` | Join table linking groups to contacts |
| `group_emails` | Bulk email sends to a group |
| `group_email_recipients` | Per-contact delivery status for each group email |

---

## Project Structure

```
gingerly/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── mail_service.py
│   │   ├── auth/routes.py
│   │   ├── contacts/routes.py
│   │   ├── emails/routes.py
│   │   ├── groups/routes.py
│   │   └── admin/routes.py
│   ├── config.py
│   ├── run.py
│   ├── seed.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── app/
    │   ├── login/page.tsx
    │   ├── register/page.tsx
    │   ├── dashboard/page.tsx
    │   ├── contacts/page.tsx
    │   ├── emails/page.tsx
    │   ├── groups/page.tsx
    │   └── admin/page.tsx
    ├── components/
    │   ├── AppShell.tsx
    │   └── Sidebar.tsx
    ├── lib/
    │   ├── api.ts
    │   └── auth.tsx
    └── .env.local
```

---

## Prerequisites

- Python 3.9+
- Node.js 18+
- A Gmail account with an [App Password](https://myaccount.google.com/apppasswords) (requires 2FA enabled)

---

## Setup & Running

### 1. Clone the repo

```bash
git clone <repo-url>
cd gingerly
```

### 2. Backend

```bash
cd backend

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=your@gmail.com
```

Seed the database (creates the default admin account):

```bash
python seed.py
```

Start the API server:

```bash
python run.py
```

API runs at `http://localhost:5001`

### 4. API Docs (Swagger UI)

Once the backend is running, open:

```
http://localhost:5001/api/docs
```

The interactive Swagger UI lets you explore and test every endpoint. It is served directly by Flask — no separate tool needed. The raw OpenAPI spec is available at `http://localhost:5001/api/docs/openapi.yaml`.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

App runs at `http://localhost:3000`

---

## Default Admin Account

Created by `seed.py`:

| Field | Value |
|-------|-------|
| Email | `admin@gingerly.com` |
| Password | `admin123` |
| Role | Admin + Superuser |

---

## API Reference

**Auth**
```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me
```

**Contacts**
```
GET    /api/contacts
POST   /api/contacts
PUT    /api/contacts/:id
DELETE /api/contacts/:id
```

**Emails**
```
GET    /api/emails
POST   /api/emails
DELETE /api/emails/:id
POST   /api/emails/:id/retry        # Gold plan only
```

**Groups** *(Gold plan only)*
```
GET    /api/groups
POST   /api/groups
DELETE /api/groups/:id
POST   /api/groups/:id/contacts
DELETE /api/groups/:id/contacts/:contact_id
POST   /api/groups/:id/emails
GET    /api/groups/:id/emails
GET    /api/groups/:id/emails/:email_id/status
```

**Admin**
```
GET    /api/admin/users
GET    /api/admin/users/:id
DELETE /api/admin/users/:id

# Superuser only
POST   /api/admin/users/:id/upgrade
POST   /api/admin/users/:id/downgrade
POST   /api/admin/users/:id/grant-admin
POST   /api/admin/users/:id/revoke-admin
POST   /api/admin/users/:id/grant-superuser
POST   /api/admin/users/:id/revoke-superuser
```

---

## Roles & Permissions

| Capability | Normal | Admin | Admin + Superuser |
|-----------|--------|-------|-------------------|
| Manage own contacts & emails | ✓ | ✓ | ✓ |
| Retry failed emails | Gold only | Gold only | Gold only |
| Create groups & bulk email | Gold only | Gold only | Gold only |
| View all users + email history | — | ✓ | ✓ |
| Delete any user | — | ✓ | ✓ |
| Upgrade / downgrade plan | — | — | ✓ |
| Grant / revoke admin | — | — | ✓ |
| Grant / revoke superuser | — | — | ✓ |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret |
| `JWT_SECRET_KEY` | JWT signing key |
| `MAIL_SERVER` | SMTP host (default: `smtp.gmail.com`) |
| `MAIL_PORT` | SMTP port (default: `587`) |
| `MAIL_USE_TLS` | Enable TLS (default: `true`) |
| `MAIL_USERNAME` | SMTP login / sender address |
| `MAIL_PASSWORD` | App password or API key |
| `MAIL_DEFAULT_SENDER` | From address on outgoing emails |

If `MAIL_USERNAME` is not set, the app runs in dev mode — emails are logged to the console instead of being delivered.
