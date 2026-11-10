# Nangarhar University Digital Library — Backend

FastAPI REST API for the university's digital library.

## Features
- Student and teacher self-registration; admin is created only by server command
- JWT authentication and role-based access control
- PDF uploads with extension, signature, and size checks
- University-wide or private documents
- Search by title/description, category, department, and subject
- Download counters and per-user download logs
- Bookmarks and document reporting
- Admin statistics, user activation/deactivation, document approval, and reports
- SQLite for local development; PostgreSQL supported for deployment

## Setup
Python 3.10+ is required.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env`. Set a unique random `SECRET_KEY` (32+ characters) and a strong `ADMIN_PASSWORD` (12+ characters). For PostgreSQL set `DATABASE_URL`, for example:
`postgresql+psycopg://username:password@localhost:5432/nangarhar_library`

Create the first admin:
```bash
python -m app.create_admin
```

Start the API:
```bash
uvicorn app.main:app --reload
```

Open:
- API: http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Main endpoints

| Method | Endpoint | Access |
|---|---|---|
| POST | `/api/auth/register` | Public (student/teacher only) |
| POST | `/api/auth/login` | Public |
| GET | `/api/auth/me` | Logged in |
| GET | `/api/documents` | Logged in |
| POST | `/api/documents` | Logged in |
| GET | `/api/documents/{id}` | Logged in |
| GET | `/api/documents/{id}/download` | Logged in |
| DELETE | `/api/documents/{id}` | Owner or admin |
| POST | `/api/documents/{id}/bookmark` | Logged in |
| GET | `/api/bookmarks` | Logged in |
| POST | `/api/documents/{id}/report` | Logged in |
| GET | `/api/admin/stats` | Admin |
| GET | `/api/admin/users` | Admin |
| PATCH | `/api/admin/users/{id}/status` | Admin |
| GET | `/api/admin/documents/pending` | Admin |
| PATCH | `/api/admin/documents/{id}/approval` | Admin |
| GET | `/api/admin/reports` | Admin |
| PATCH | `/api/admin/reports/{id}/resolve` | Admin |
| GET | `/api/admin/downloads/recent` | Admin |

## Frontend integration
Send the token on protected API calls:
`Authorization: Bearer <access_token>`

Upload using `multipart/form-data` with fields:
`title`, `description`, `category`, `department`, `subject`, `visibility`, and `file`.

For admin document approval use JSON:
`{"is_approved": true}`

For user status use JSON:
`{"is_active": false}`

## Before real university deployment
This is a development backend starter, not a completed institutional security review. Before production:
- Use PostgreSQL and Alembic migrations; do not rely on `create_all` for schema evolution.
- Serve over HTTPS; store secrets in a secret manager.
- Add university email/ID verification and admin invitation workflows.
- Add rate limiting, audit logs, malware scanning, backups, and monitoring.
- Consider private object storage (S3-compatible) and signed downloads.
- Review privacy, copyright, retention, and university IT policies.
- Restrict CORS to the actual production frontend domain.
