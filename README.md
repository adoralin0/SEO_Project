# Loyable — local restaurant rewards

Flask + static frontend skeleton for Week 4 rubric setup.

## Structure

```
_temp_barebones/
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
│       ├── conftest.py
│       ├── test_auth.py
│       └── test_restaurants.py
├── frontend/
│   ├── index.html
│   ├── explore.html
│   ├── styles.css
│   └── app.js
├── docs/
│   ├── standup-notes.md
│   ├── task-board.md
│   ├── wireframe.md
│   └── system-diagram.md
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

## Run tests

```bash
cd backend
pytest
```

## Frontend

Open `frontend/index.html` in a browser, or use Live Server.
