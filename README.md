# 💰 AI Expense Tracker — Project Specification

## Overview

A conversational AI expense tracker where users log expenses via natural language. Bedrock handles NLP extraction, LangGraph orchestrates the agent flow, FastAPI serves the backend, and everything deploys on AWS. Telegram bot is Phase 2 — plugs in without changing the core backend.

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Orchestration | LangGraph |
| LLM | AWS Bedrock (Claude) |
| Backend | FastAPI |
| ORM / DB Layer | SQLAlchemy |
| Database | AWS RDS (PostgreSQL) |
| File Storage | AWS S3 (receipt images, future) |
| Hosting | AWS EC2 |
| Auth & Permissions | AWS IAM |
| CI/CD | GitHub Actions |
| Testing | Pytest |
| Bot Interface (Phase 2) | Telegram Bot API |

---

## Phases

### Phase 1 — Core Backend
REST API + AI agent pipeline. Fully functional without any chat interface.

### Phase 2 — Telegram Bot
Wire Telegram webhooks to existing Phase 1 endpoints. No backend changes needed.

---

## Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | Display name |
| email | String | Unique |
| monthly_budget | Float | Overall monthly budget |
| created_at | DateTime | |

### `categories`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| name | String | Food, Transport, Shopping, Utilities, Entertainment, Others |
| icon | String | Emoji for display |

### `expenses`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK → users |
| amount | Float | In SGD |
| category_id | UUID | FK → categories |
| description | String | Raw user input |
| vendor | String | Extracted vendor name |
| date | Date | Expense date (not entry date) |
| created_at | DateTime | Entry timestamp |
| confidence_score | Float | Bedrock extraction confidence |
| flagged | Boolean | True if agent is unsure |

### `budgets`
| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id | UUID | FK → users |
| category_id | UUID | FK → categories |
| month | Date | First day of the month |
| limit | Float | Budget cap |

---

## LangGraph Agent Flow

Every expense input runs through this pipeline:

```
User Input (natural language)
        ↓
[Extract Node]
Bedrock parses: amount, vendor, category, date, description
        ↓
[Validate Node]
Is amount > 0? Is date plausible? Is category valid?
If unsure → set flagged = True
        ↓
[Categorize Node]
Map vendor/description to a category
e.g. "Grab" → Transport, "Maxwell" → Food
        ↓
[Budget Check Node]
How much has user spent this month?
Is this category over budget?
        ↓
[Response Node]
Generate a friendly confirmation + budget status
```

---

## FastAPI Endpoints

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses` | Log a new expense (natural language or structured) |
| GET | `/expenses` | List expenses (filter by date, category, user) |
| GET | `/expenses/{id}` | Get single expense |
| PUT | `/expenses/{id}` | Edit an expense |
| DELETE | `/expenses/{id}` | Delete an expense |

### Reports
| Method | Endpoint | Description |
|---|---|---|
| GET | `/reports/monthly` | Total spending this month |
| GET | `/reports/category` | Breakdown by category |
| GET | `/reports/daily` | Day by day spending |
| GET | `/reports/budget-status` | Remaining budget per category |

### Users
| Method | Endpoint | Description |
|---|---|---|
| POST | `/users` | Create user |
| GET | `/users/{id}` | Get user profile |
| PUT | `/users/{id}/budget` | Update monthly budget |

### Budgets
| Method | Endpoint | Description |
|---|---|---|
| POST | `/budgets` | Set category budget |
| GET | `/budgets` | Get all budgets for user |
| PUT | `/budgets/{id}` | Update a budget |

### Telegram (Phase 2)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/webhook/telegram` | Receive Telegram messages |

---

## Bedrock Extraction

**Input** — raw user string:
```
"Spent $12.50 on chicken rice at Tian Tian yesterday"
```

**Expected structured output:**
```json
{
  "amount": 12.50,
  "vendor": "Tian Tian",
  "description": "chicken rice",
  "category": "Food",
  "date": "2026-05-02",
  "confidence": 0.97
}
```

Bedrock also handles messy inputs like:
- `"grabbed coffee 6 bucks"` → amount: 6.00, category: Food
- `"transport last tuesday 2.40"` → date inferred, category: Transport
- `"$340 laptop bag"` → category: Shopping

---

## Business Logic Rules

- All amounts in SGD
- If `confidence_score < 0.75` → flag expense for review, still save it
- Budget warnings trigger at **80%** and **100%** of limit
- Default categories are seeded on first run
- Date defaults to today if not specified
- Monthly reports run from 1st to last day of calendar month

---

## Testing Strategy (Pytest)

| Test Type | What It Covers |
|---|---|
| Unit | Bedrock extraction parsing, LangGraph node logic |
| Integration | FastAPI endpoints with test DB |
| Agent | Full LangGraph flow with mocked Bedrock responses |
| Edge Cases | Ambiguous inputs, missing amounts, future dates |

---

## AWS Infrastructure

| Service | Purpose |
|---|---|
| EC2 | Hosts FastAPI app |
| RDS (PostgreSQL) | Persistent database |
| S3 | Store raw inputs / future receipt images |
| Bedrock | LLM inference |
| IAM | Roles for EC2 → Bedrock, EC2 → RDS, EC2 → S3 |

---

## GitHub Actions CI/CD Pipeline

```
Push to main
    ↓
Run Pytest suite
    ↓
Build Docker image
    ↓
Push to ECR (or direct to EC2)
    ↓
SSH into EC2 + restart service
```

---

## Phase 2 — Telegram Bot

**How it connects:** Telegram sends a webhook POST to `/webhook/telegram` → FastAPI processes it → calls the same LangGraph agent → replies to user via Telegram Bot API. Zero changes to Phase 1 logic.

**Supported commands:**

| Command | Action |
|---|---|
| Any natural language | Log expense |
| `/summary` | Monthly spending snapshot |
| `/budget` | Remaining budget per category |
| `/history` | Last 10 expenses |
| `/set_budget [category] [amount]` | Update budget |

---

## Project Folder Structure

```
expense-tracker/
├── app/
│   ├── main.py               # FastAPI entry point
│   ├── models/               # SQLAlchemy models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── routers/              # FastAPI route handlers
│   ├── agent/                # LangGraph nodes and graph definition
│   ├── services/             # Bedrock extraction, budget logic
│   └── db/                   # DB connection, migrations
├── tests/
│   ├── unit/
│   ├── integration/
│   └── agent/
├── .github/
│   └── workflows/
│       └── deploy.yml
├── docker/
│   └── Dockerfile
├── requirements.txt
└── README.md
```

---

## Build Order

1. DB schema + SQLAlchemy models
2. Bedrock extraction service (prompt + parser)
3. LangGraph agent (node by node)
4. FastAPI endpoints (expenses first, then reports)
5. Pytest suite
6. Dockerise + GH Actions pipeline
7. Deploy to EC2 + RDS
8. Telegram bot webhook (Phase 2)