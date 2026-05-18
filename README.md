# 💸 Expense Tracker

An AI-powered expense tracking API that lets users log expenses in natural language. Built with FastAPI, LangGraph, and LLM-based extraction (Ollama for local dev, AWS Bedrock in production).

---

## Features

- **Natural language expense logging** — just describe what you spent ("Grabbed a coffee for $4.50 after gym") and the agent extracts the amount, category, date, and description automatically
- **LangGraph agent pipeline** — extraction → validation → retry loop with up to 3 attempts before flagging
- **Budget tracking** — set monthly budgets globally and per category, with alerts when approaching or exceeding limits
- **Flexible filtering** — query expenses by date range, category, or amount
- **Dual LLM backend** — Ollama (local dev) and AWS Bedrock Claude (production)
- **Full test coverage** — unit, agent, and integration tests across all endpoints

---

## Tech Stack

| Layer | Tech |
|---|---|
| API | FastAPI |
| Agent | LangGraph + LangChain |
| LLM (dev) | Ollama (`llama3.2:3b`) |
| LLM (prod) | AWS Bedrock (`claude-3-5-sonnet`) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| ORM | SQLAlchemy |
| Validation | Pydantic v2 |
| Testing | Pytest + pytest-mock |

---

## Project Structure

```
├── app/
│   ├── agent/
│   │   └── expense_agent/
│   │       ├── graph.py        # LangGraph state machine
│   │       ├── nodes.py        # Extraction, validation, decision nodes
│   │       ├── prompts.py      # LLM prompts
│   │       └── schemas.py      # Agent state + extracted expense schemas
│   ├── db/
│   │   └── database.py         # SQLAlchemy engine + session setup
│   ├── models/                 # SQLAlchemy ORM models (User, Expense, Budget)
│   ├── routers/                # FastAPI route handlers
│   ├── schemas/                # Pydantic request/response schemas
│   └── main.py
├── utils/
│   ├── config.py               # Pydantic settings + env config
│   ├── db_helpers.py           # Dialect-aware SQL helpers
│   └── logger.py
└── tests/
    ├── unit/                   # Node-level unit tests
    ├── agent/                  # End-to-end graph tests
    └── integration/            # API endpoint tests
```

---

## Agent Pipeline

The expense agent runs as a LangGraph state machine with three nodes:

```
START → extraction → validation → decision
                          ↑            |
                          └─ retry ────┘ (max 3 attempts)
                                        └→ END
```

1. **Extraction** — LLM extracts amount, category, date, description, and confidence score from the raw input
2. **Validation** — checks for null/invalid fields and confidence below threshold (default: 0.75)
3. **Decision** — routes to END on success, or back to extraction (with the failure reason injected into the retry prompt) up to 3 times

---

## API Endpoints

### Users
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/users/{user_id}` | Get user by ID |
| `POST` | `/users/` | Create user |
| `PUT` | `/users/{user_id}` | Update user details |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/expenses/` | Get expenses with optional filters |
| `GET` | `/expenses/{expense_id}` | Get expense by ID |
| `POST` | `/expenses/` | Create expense (runs agent pipeline) |
| `PUT` | `/expenses/{expense_id}` | Update expense manually |
| `DELETE` | `/expenses/{expense_id}` | Delete expense |

### Budgets
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/budgets/{user_id}` | Get all budgets for a user |
| `POST` | `/budgets/` | Create category budget |
| `PUT` | `/budgets/{user_id}` | Update category budget |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) running locally (dev)
- Docker (optional)

### Installation

```bash
git clone https://github.com/your-username/expense-tracker.git
cd expense-tracker
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root:

```env
APP_ENV=dev
DATABASE_URL=sqlite:///./app/db/test.db
LOG_LEVEL=DEBUG

# Ollama (dev)
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

# Bedrock (prod)
AWS_REGION=ap-southeast-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# Agent
CONFIDENCE_THRESHOLD=0.75
MODEL_TEMPERATURE=0.0
```

### Run

```bash
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

---

## Running Tests

```bash
pytest
```

Tests are structured across three layers:

- `tests/unit/` — individual node logic (extraction, validation, decision)
- `tests/agent/` — full LangGraph graph traversal (mocked LLM)
- `tests/integration/` — full HTTP request/response cycle per endpoint

---

## Expense Categories

`Food` · `Transport` · `Shopping` · `Utilities` · `Entertainment` · `Others`

---

## Roadmap

- [x] Natural language expense extraction with LangGraph
- [x] Per-category and monthly budget alerts
- [x] Retry loop with targeted failure feedback
- [ ] **Financial Report Agent** *(coming soon)* — AI-generated monthly summaries with spending insights, trends, and budget recommendations

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

