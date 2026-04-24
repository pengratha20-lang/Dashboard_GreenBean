# Deploy GreenBean To Render

## 1. Push your current code to GitHub
Render deploys from a GitHub repository. Ensure your latest changes are committed and pushed.

## 2. Create a PostgreSQL database on Render
1. In Render, click New +.
2. Choose PostgreSQL.
3. Create the database.
4. Copy the Internal Database URL (Render can auto-inject this as DATABASE_URL).

## 3. Create the web service
1. In Render, click New +.
2. Choose Web Service.
3. Select this GitHub repository.
4. Render will detect render.yaml automatically.

If Render does not use render.yaml, set these manually:
- Build Command: `pip install -r requirements.txt`
- Start Command: `flask db upgrade ; gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120`

## 4. Configure environment variables
Required:
- FLASK_SECRET_KEY: at least 32 characters
- DATABASE_URL: your Render Postgres URL

Recommended:
- FLASK_ENV=production
- FLASK_DEBUG=False
- SESSION_COOKIE_SECURE=True
- SESSION_COOKIE_SAMESITE=Lax

Optional payment/integration variables (if used in your app):
- BAKONG_API_KEY
- BAKONG_ACCOUNT_ID
- STRIPE_SECRET_KEY
- TELEGRAM_BOT_TOKEN

## 5. First deploy verification
After deployment:
1. Open the Render service URL.
2. Confirm the home page loads.
3. Open `/admin/login` and verify admin login page works.
4. Check Render logs for migration output from `flask db upgrade`.

## Notes
- Your app now reads DATABASE_URL from environment.
- It still falls back to SQLite (`sqlite:///app.db`) for local development.
- `postgres://` URLs are normalized to `postgresql://` for SQLAlchemy compatibility.
