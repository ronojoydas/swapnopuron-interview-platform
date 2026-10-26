# Swapnopuron Interview Platform — Deployment Guide

## Architecture

- Frontend: React, TypeScript, and Vite.
- Backend: FastAPI, served by Uvicorn.
- Database: PostgreSQL, managed separately from the application service.
- Hosting target: Render for the backend. The frontend can be deployed as a static site.

## Before deployment

1. Review the application and authorization tests.
2. Confirm that production secrets are not tracked by Git.
3. Create a managed PostgreSQL database for production.
4. Use a separate production database; never point deployment commands at a local or live operational database by accident.
5. Configure the environment variables listed below.
6. Verify that candidate CVs, uploaded documents, and other files use persistent, access-controlled storage if the application supports uploads.
7. Confirm authentication, authorization, privacy, backups, and recovery procedures before using real candidate data.

## Render backend service

Create a Python web service connected to the repository.

- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`

Set these environment variables in the Render dashboard:

- `DATABASE_URL`: the production PostgreSQL connection URL, using the SQLAlchemy `postgresql+psycopg://` driver format.
- `FRONTEND_ORIGINS`: the exact deployed frontend origin, including `https://` and excluding any path. Multiple origins may be comma-separated.

Do not commit production secrets or put them in this guide.

## Database migrations

The repository currently has two Alembic migrations. Before initializing production:

1. Verify the production database connection and confirm it is the intended empty/new database.
2. Take a backup if the database contains anything important.
3. Review the migration files and model definitions.
4. Run `alembic upgrade head` from the backend directory with the production `DATABASE_URL` explicitly configured.
5. Verify the current Alembic revision and test the application's database-backed endpoints.

Do not run migrations against the local or production database until the target is confirmed.

## Frontend static site

Create a static site for the `frontend` directory.

- Root directory: `frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `dist`
- Build-time environment variable: `VITE_API_URL=https://YOUR-BACKEND-SERVICE.onrender.com`

Replace the example backend URL with the actual deployed service URL. Do not append `/auth/login`; the frontend constructs endpoint paths itself.

If client-side routes are introduced, configure the static host to rewrite application routes to `index.html`.

## Post-deployment checks

- Open `/health` on the deployed API and confirm it returns a healthy status.
- Test login and logout.
- Verify staff and candidate permissions using separate test accounts.
- Test application creation, status changes, interview scheduling, and feedback workflows.
- Verify CORS from the deployed frontend origin.
- Verify error handling and logs without exposing personal data or tokens.
- Confirm database backups and restoration procedures.
- Confirm uploaded files remain available after a service restart or redeploy.

## Go-live rule

Use synthetic or test data until production security, persistence, access controls, backup and recovery, and operational ownership have been verified.
