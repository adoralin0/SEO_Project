# Loyable — local restaurant rewards

Flask + static frontend skeleton for Week 4 rubric setup.

## Structure

```
SEO_Project/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── models.py
│   ├── requirements.txt
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── restaurants.py
│   └── tests/
├── frontend/
│   ├── index.html
│   ├── explore.html
│   ├── login.html
│   ├── profile.html
│   ├── dashboard.html
│   ├── styles.css
│   └── app.js
└── README.md
```

## Run backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open **http://localhost:5000/**

## Auth0 (Gmail / Google login)

1. Create a free [Auth0](https://auth0.com/) tenant.
2. **Applications → Create Application** → *Single Page Application*.
3. In the app **Settings**:
   - Leave **Application Login URI** empty
   - **Allowed Callback URLs:** `http://localhost:5000/login.html` (press Enter after the URL)
   - **Allowed Logout URLs:** `http://localhost:5000/`
   - **Allowed Web Origins:** `http://localhost:5000`
   - Auth0 allows `http://localhost` without HTTPS for local development
4. **Authentication → Social → Google** → enable and follow Auth0’s Google setup (or use Auth0’s built-in Google keys for trying it out).
5. Copy `.env.example` to `backend/.env` and set:

```env
AUTH0_DOMAIN=your-tenant.us.auth0.com
AUTH0_CLIENT_ID=your_spa_client_id
```

6. Restart Flask. The login page shows **Continue with Google** when Auth0 is configured.

Email/password signup still works alongside Google.

## Run tests

```bash
cd backend
pytest
```

## Frontend

Served by Flask at `http://127.0.0.1:5000/`, or open `frontend/` files via Live Server (API calls expect the Flask origin).
