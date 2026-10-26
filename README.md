\# Swapnopuron Interview Platform



A web application for managing recruitment and interview workflows at Swapnopuron.



\## Technology Stack



\- Frontend: React, TypeScript, Vite

\- Backend: FastAPI, Python, SQLAlchemy

\- Database: PostgreSQL

\- Migrations: Alembic



\## Project Structure



\- `backend/` — FastAPI application and database migrations

\- `database/` — Database-related resources

\- `docs/` — Deployment documentation

\- `frontend/` — React and Vite application



\## Local Development



\### Backend



Configure `DATABASE\_URL` in `backend/.env` before starting the API.



From the project root, run:



```powershell

.\\backend\\venv\\Scripts\\python.exe -m uvicorn app.main:app --reload

```



Health endpoint: `http://127.0.0.1:8000/health`



\### Frontend



Open a separate terminal:



```powershell

cd frontend

npm ci

npm run dev

```



The frontend is typically available at `http://localhost:5173`.



For deployment, set `VITE\_API\_URL` to your deployed backend's base URL before building.



\## Deployment



See \[docs/deployment.md](docs/deployment.md) for Render configuration, PostgreSQL setup, migrations, and go-live checks.



\## Security



\- Never commit `.env` files, credentials, authentication tokens, or real candidate information.

\- Use a separate production database.

\- Verify authorization, persistence, backups, and recovery before using real candidate data.

\- Deployment instructions alone do not establish production readiness.
