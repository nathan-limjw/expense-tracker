# 💸 Expense Tracker

An AI-powered expense tracking API that lets users log expenses in plain natural language. The agent automatically extracts the amount, category, date, and description — no forms, no dropdowns.

---

## What I Built & Why

Most expense trackers make you fill in structured fields. I wanted to explore whether an LLM agent could handle that extraction reliably — and what it takes to make that production-ready.

This project is a backend API with a LangGraph-powered extraction pipeline, budget alerting, full test coverage, and an automated CI/CD setup deploying to AWS EC2.

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
| CI/CD | GitHub Actions → ECR → EC2 |

---

## Agent Pipeline

The core of the project is a LangGraph state machine that processes natural language expense input through three nodes:

```
START → extraction → validation → decision
                          ↑            |
                          └─ retry ────┘ (max 3 attempts)
                                        └→ END
```

1. **Extraction** — LLM pulls out amount, category, date, description, and a confidence score from raw input
2. **Validation** — rejects null/invalid fields and inputs below the confidence threshold (default: 0.75)
3. **Decision** — on failure, injects the specific failure reason back into the retry prompt and loops; gives up after 3 attempts

This means the agent self-corrects with targeted feedback rather than just retrying blindly.

---

## Features

- **Natural language logging** — "Grabbed lunch at a hawker centre for $5.50" → extracts everything automatically
- **Budget alerts** — set a monthly budget globally or per category; get warnings at 80% and 100% spend
- **Flexible filtering** — query expenses by date range, category, or amount ceiling
- **Dual LLM backend** — Ollama locally, AWS Bedrock in production, swapped via a single env var

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
    ├── agent/                  # End-to-end graph traversal tests
    └── integration/            # Full HTTP request/response tests
```

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

## Testing

Tests are structured across three layers, with the LLM mocked out for deterministic results:

```bash
pytest
```

- `tests/unit/` — individual node logic (extraction, validation, decision routing)
- `tests/agent/` — full LangGraph graph traversal with mocked LLM responses
- `tests/integration/` — full HTTP request/response cycle per endpoint, including error paths

---

## CI/CD

Automated via two GitHub Actions workflows:

**CI** — runs on every push to `dev` and `main`, executes the full test suite

**CD** — triggers automatically after CI passes on `main`; builds a Docker image, pushes to Amazon ECR, SSHs into EC2, and restarts the container

Deployments only happen when all tests pass.

---

## Roadmap

- [x] Natural language expense extraction with LangGraph
- [x] Per-category and monthly budget alerts
- [x] Self-correcting retry loop with targeted failure feedback
- [x] Automated CI/CD to AWS EC2
- [ ] **Financial Report Agent** *(coming soon)* — AI-generated monthly summaries with spending insights, trends, and budget recommendations
