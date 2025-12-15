# Database Setup & Migration Guide

This project supports both **SQLite** (default for local dev) and **PostgreSQL** (Production/Supabase).

## Automatic Setup
The application is configured to **automatically create tables** on startup if they do not exist. You generally do **not** need to run any manual SQL commands.

Just configure your connection string in `.env` and restart the backend:
```env
# For Supabase / PostgreSQL
DATABASE_URL=postgresql://postgres:[PASSWORD]@db.xxxx.supabase.co:5432/postgres

# For Local SQLite (Default)
# DATABASE_URL=sqlite:///./psx_copilot.db
```

## Manual Setup (If needed)
If you prefer to manually create the tables in your Supabase SQL Editor, you can use the generated `schema.sql` file.

1. Go to your [Supabase Dashboard](https://supabase.com/dashboard).
2. Open the **SQL Editor**.
3. Copy the contents of `backend/schema.sql`.
4. Run the query.

## Troubleshooting
- **ModuleNotFoundError: No module named 'psycopg2'**: Make sure you installed the postgres driver:
  ```bash
  pip install psycopg2-binary
  ```
- **Connection Refused**: Check your password and ensure "Database Password" is correct (not your Supabase login password).
- **Tables not found**: Check logs to see if `init_db()` ran successfully.
