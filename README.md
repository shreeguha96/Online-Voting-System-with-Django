# 🗳️ Online Voting System

A fully functional REST API built with **Python Django + SQLite** for managing elections, candidates, voters, and votes — with Swagger docs and audit logging.

---

##  Quick Start - Run Locally

```bash
# 1. Clone / unzip and cd into the project
cd voting_system

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Seed sample data (optional)
python manage.py seed_data

# 6. Create admin superuser
python manage.py createsuperuser

# 7. Run the server
python manage.py runserver
```

Open:
- **Swagger UI** → http://127.0.0.1:8000/swagger/
- **ReDoc** → http://127.0.0.1:8000/redoc/
- **Django Admin** → http://127.0.0.1:8000/admin/
- **API Root** → http://127.0.0.1:8000/api/

---

## 📡 API Endpoints

### Elections
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/elections/` | List all elections |
| POST | `/api/elections/` | Create election |
| GET | `/api/elections/{id}/` | Get election detail |
| PUT/PATCH | `/api/elections/{id}/` | Update election |
| DELETE | `/api/elections/{id}/` | Delete election |
| POST | `/api/elections/{id}/activate/` | Activate election |
| POST | `/api/elections/{id}/close/` | Close election |
| GET | `/api/elections/{id}/results/` | Get results |
| GET | `/api/elections/{id}/voters/` | List voters who voted |
| POST | `/api/elections/{id}/candidates/` | Add candidate |

### Candidates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/candidates/` | List all candidates |
| POST | `/api/candidates/` | Add candidate |
| GET/PUT/DELETE | `/api/candidates/{id}/` | Manage candidate |

### Voters
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/voters/` | List all voters |
| POST | `/api/voters/` | Register voter |
| GET/PUT | `/api/voters/{id}/` | Manage voter |
| GET | `/api/voters/{id}/vote-history/` | Voter's vote history |
| GET | `/api/voters/{id}/check-eligibility/{election_id}/` | Check eligibility |

### Votes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/votes/` | List all votes |
| POST | `/api/votes/cast/` | **Cast a vote** |

### Misc
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/audit-logs/` | Audit trail |
| GET | `/api/dashboard/stats/` | System statistics |

---

## 🗳️ Cast a Vote (Example)

```bash
curl -X POST http://127.0.0.1:8000/api/votes/cast/ \
  -H "Content-Type: application/json" \
  -d '{"voter_id": "VOT0001", "candidate_id": "<uuid>"}'
```

---

## Deployment

### Render 
1. Push code to GitHub
2. Go to https://render.com → New Web Service
3. Connect your GitHub repo
4. Set **Build Command**: `pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput`
5. Set **Start Command**: `gunicorn voting_system.wsgi:application`
6. Add env var: `SECRET_KEY` = any random string, `DEBUG` = False
7. Deploy → Free plan supports SQLite


## 🔐 Django Admin
- URL: `/admin/`
- Create superuser: `python manage.py createsuperuser`
- Manage all models visually with audit-safe read-only vote records

