# Voice Inventory System — Complete Setup & Development Guide

## 1. Project Overview

The **Voice Inventory System** is a voice-first sales and inventory application for a small physical retail stall / pop-up shop business.

The goal is to let the business owner speak commands such as:

> “ABC bought two ceramic cup sets for sixty dollars and paid by card.”

The system then:

1. Records audio in the browser.
2. Converts speech to text using Whisper.
3. Extracts a structured sales command using an LLM.
4. Resolves customer and product names against PostgreSQL.
5. Detects missing or ambiguous information.
6. Requests clarification when required.
7. Shows a confirmation summary.
8. Writes to PostgreSQL only after explicit confirmation.
9. Updates inventory.
10. Records payment and inventory movements.
11. Creates an audit event.
12. Lets the owner review recent sales.
13. Supports read-only voice questions such as:
   - “How many ceramic cup sets do I have left?”
   - Planned: “What did ABC buy last time?”

Core architecture rule:

```text
LLM interprets
    ↓
Application logic validates
    ↓
User confirms
    ↓
Database transaction writes
```

The LLM does **not** generate or execute arbitrary SQL.

---

## 2. Technology Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS
- App Router
- Browser `MediaRecorder` API
- Mobile-first design
- Planned PWA evolution

### Backend
- Python 3.11
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- Pydantic Settings
- Alembic
- HTTPX

### Database
- PostgreSQL
- pgAdmin

### AI / Voice
- Ollama
- Qwen3 4B
- faster-whisper

### Future Production Target
- AWS ECS
- Amazon ECR
- Amazon RDS PostgreSQL
- CloudWatch
- ALB / HTTPS
- Production AI inference architecture to be finalized later

---

## 3. Project Location

Local project directory:

```text
C:\Users\sandh\VoiceInventoryApp
```

High-level structure:

```text
VoiceInventoryApp/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── db.py
│   │   └── main.py
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env
│   └── .venv/
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   └── sales/
│   │       ├── page.tsx
│   │       └── [saleId]/
│   │           ├── page.tsx
│   │           └── sale-detail-client.tsx
│   ├── package.json
│   └── ...
├── docs/
└── .gitignore
```

---

## 4. Prerequisites

### Git

```powershell
git --version
```

Development machine version:

```text
git version 2.47.0.windows.1
```

### Python

```powershell
python --version
```

Development version:

```text
Python 3.11.9
```

Important: use `python`, not `py`.

### Node.js

```powershell
node --version
npm --version
```

If missing:

```powershell
winget install OpenJS.NodeJS.LTS
```

Close and reopen the terminal after installation.

### PostgreSQL

Install PostgreSQL and pgAdmin.

Local port:

```text
5432
```

### Ollama

Install:

```powershell
winget install Ollama.Ollama
```

Verify:

```powershell
ollama --version
```

Pull model:

```powershell
ollama pull qwen3:4b
```

Test:

```powershell
ollama run qwen3:4b
```

Exit:

```text
/bye
```

---

## 5. Clone the Repository

For a fresh machine:

```powershell
cd C:\Users\<your-user>
git clone https://github.com/Ishwinder-kaur/VoiceInventoryApp.git
cd VoiceInventoryApp
```

Check branches:

```powershell
git branch -a
```

If using `master`:

```powershell
git checkout master
git pull origin master
```

If the repository later uses `main`:

```powershell
git checkout main
git pull origin main
```

---

## 6. Pull Latest Code on an Existing Clone

```powershell
cd C:\Users\sandh\VoiceInventoryApp
git branch --show-current
```

For `master`:

```powershell
git pull origin master
```

For `main`:

```powershell
git pull origin main
```

---

## 7. GitHub Authentication

Install GitHub CLI:

```powershell
winget install --id GitHub.cli
```

Close and reopen the terminal.

Verify:

```powershell
gh --version
```

Login:

```powershell
gh auth login
```

Choose:

```text
GitHub.com
HTTPS
Login with a web browser
```

Verify:

```powershell
gh auth status
```

Intended account:

```text
Ishwinder-kaur
```

If `git remote -v` shows nothing:

```powershell
git remote add origin https://github.com/Ishwinder-kaur/VoiceInventoryApp.git
```

Verify:

```powershell
git remote -v
```

Push:

```powershell
git push -u origin master
```

---

## 8. Backend Setup

```powershell
cd C:\Users\sandh\VoiceInventoryApp\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install from requirements:

```powershell
python -m pip install -r requirements.txt
```

Core packages used:

```text
fastapi
uvicorn[standard]
sqlalchemy
psycopg[binary]
pydantic-settings
alembic
httpx
faster-whisper
python-multipart
```

Manual install if required:

```powershell
python -m pip install fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" pydantic-settings alembic httpx faster-whisper python-multipart
```

---

## 9. PostgreSQL Setup

Create database:

```sql
CREATE DATABASE voice_inventory;
```

Local connection settings:

```text
Database: voice_inventory
Host: localhost
Port: 5432
User: postgres
```

Do not commit database passwords.

---

## 10. Backend `.env`

Create:

```text
backend/.env
```

Example:

```env
DATABASE_URL=postgresql+psycopg://postgres:<URL_ENCODED_PASSWORD>@localhost:5432/voice_inventory
```

If the password contains `@`, encode it as `%40`.

Never commit `.env`.

---

## 11. Backend Configuration

`backend/app/core/config.py`

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()
```

Future AWS-ready configuration should move these to environment variables:

```text
DATABASE_URL
OLLAMA_URL
MODEL_NAME
NEXT_PUBLIC_API_URL
ALLOWED_ORIGINS
```

---

## 12. SQLAlchemy Setup

`backend/app/db.py`

```python
from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## 13. Alembic Migrations

Alembic was initialized with:

```powershell
alembic init alembic
```

Migration history created during development includes:

```text
create_core_business_tables
add_sales_inventory_voice_and_audit
add_customer_and_product_aliases
add_product_quantity_on_hand
add_pending_voice_commands
```

Apply migrations:

```powershell
cd C:\Users\sandh\VoiceInventoryApp\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
```

Verify:

```powershell
alembic current
```

---

## 14. Main Database Tables

### businesses
Stores business settings such as name, currency and timezone.

### owners
Business owners/users.

### customers
Customer master data.

### customer_aliases
Maps aliases such as:

```text
ABC -> ABC Customer
```

### products
Includes:

```text
sku
name
unit_price
quantity_on_hand
currency
active
```

### product_aliases
Maps alternate spoken names to products.

### stall_events
Represents physical pop-up / stall events.

### sales
Stores confirmed sale headers.

### sale_items
Stores sale line items.

### payments
Stores sale payment details.

### inventory_movements
Audit/history ledger for stock changes.

### voice_interactions
Designed to store transcript, model details, extracted commands and audio references.

### audit_events
Tracks database mutations.

### pending_voice_commands
Stores exact commands awaiting clarification or confirmation.

Statuses currently include:

```text
NEEDS_CLARIFICATION
PENDING_CONFIRMATION
CONFIRMED
CANCELLED
FAILED
```

---

## 15. Example Development Data

Example business:

```text
Business ID: 1
Name: My Stall Business
Currency: USD
Timezone: America/New_York
```

Example customer:

```text
Customer ID: 1
Name: ABC Customer
Alias: ABC
```

Example product:

```text
Product ID: 2
SKU: CUP-002
Name: Ceramic Cup Set
Unit Price: 30
Currency: USD
```

Current inventory quantity changes as test sales are created.

---

## 16. Start Backend

```powershell
cd C:\Users\sandh\VoiceInventoryApp\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

Health:

```text
GET /health
```

Expected:

```json
{"status": "ok"}
```

---

## 17. CORS

Local frontend origins allowed by FastAPI:

```text
http://localhost:3000
http://127.0.0.1:3000
```

These must be replaced with production origins for AWS.

---

## 18. Business / Customer / Product APIs

### Businesses

```text
POST /businesses
GET /businesses/{business_id}
```

### Customers

```text
POST /customers
GET /customers/{customer_id}
GET /customers?business_id=1&query=...
POST /customers/{customer_id}/aliases
```

### Products

```text
POST /products
GET /products/{product_id}
GET /products?business_id=1&query=...
POST /products/{product_id}/aliases
```

---

## 19. Sale Transaction Rules

The sale service performs deterministic checks and writes:

```text
validate business
validate customer
validate event
validate product
validate product ownership
validate active status
validate stock
calculate totals
determine payment status
create sale
create sale items
decrement stock
create inventory movement
create payment
create audit event
commit transaction
rollback on failure
```

The LLM never performs the database transaction.

---

## 20. Sale APIs

Create:

```text
POST /sales
```

Recent sales:

```text
GET /sales?business_id=1&limit=20
```

Sale details:

```text
GET /sales/{sale_id}
```

Sale details now include human-readable customer/product names in addition to IDs.

---

## 21. Audit API

```text
GET /audit?business_id=1
```

Optional filters:

```text
entity_type
entity_id
```

Example:

```text
GET /audit?business_id=1&entity_type=SALE
```

---

## 22. Ollama / Qwen

Model:

```text
qwen3:4b
```

Verify:

```powershell
ollama list
```

Local API:

```text
http://localhost:11434/api/chat
```

Important settings used:

```text
stream=false
think=false
keep_alive=30m
temperature=0
```

`think=false` fixed very slow structured requests.

`keep_alive=30m` reduces repeated model-load latency.

---

## 23. Voice Sale Extraction

Endpoint:

```text
POST /voice/extract
```

Example:

```json
{
  "text": "ABC bought 2 ceramic cup sets for 60 dollars and paid by card."
}
```

The model output is validated with a Pydantic schema.

Field states used:

```text
PROVIDED
INFERRED
MISSING
AMBIGUOUS
```

---

## 24. Entity Resolution

Resolution checks:

```text
canonical customer/product name
aliases
normalized spoken phrase
simple plural handling
```

Example:

```text
ceramic cup sets
```

resolves to:

```text
Ceramic Cup Set
```

Long clarification phrases can also be resolved, for example:

```text
I mean the Ceramic Cup Set.
```

---

## 25. Deterministic Payment Normalization

Common payment phrases are normalized in application code.

Examples:

```text
paid by card
paid with card
card payment
```

become:

```text
payment_method = CARD
payment_status = PAID
```

Examples:

```text
paid cash
paid by cash
paid in cash
```

become:

```text
payment_method = CASH
payment_status = PAID
```

If a sale is explicitly paid in full but the amount is missing, the application uses the deterministic calculated sale total.

---

## 26. Prepare Sale Flow

Endpoint:

```text
POST /voice/prepare?business_id=1
```

It:

1. Extracts the command.
2. Resolves entities.
3. Validates.
4. Calculates totals.
5. Generates clarification questions if needed.
6. Stores exact prepared data in `pending_voice_commands`.
7. Returns a `confirmation_id`.

Possible state:

```text
PENDING_CONFIRMATION
```

or:

```text
NEEDS_CLARIFICATION
```

---

## 27. Confirm Sale Flow

Endpoint:

```text
POST /voice/confirm
```

Example:

```json
{
  "confirmation_id": 9,
  "confirmed": true
}
```

The LLM is **not called again** during confirmation.

The exact reviewed command is loaded from PostgreSQL.

A successful confirmation:

```text
creates sale
creates items
creates payment
updates stock
creates inventory movement
creates audit event
marks pending command CONFIRMED
```

Cancellation marks it:

```text
CANCELLED
```

---

## 28. Clarification Flow

Endpoint:

```text
POST /voice/clarify
```

Example:

```json
{
  "confirmation_id": 12,
  "answer": "I mean the Ceramic Cup Set."
}
```

Architecture:

```text
try deterministic resolution
    ↓
if uniquely resolvable:
    update immediately
else:
    fallback to Qwen
```

Response indicates:

```text
clarification_mode = DETERMINISTIC
```

or:

```text
clarification_mode = LLM
```

---

## 29. Local Speech-to-Text

Installed:

```powershell
python -m pip install faster-whisper python-multipart
```

Current model:

```text
base
```

Current configuration:

```text
device=cpu
compute_type=int8
```

Endpoint:

```text
POST /voice/transcribe
```

---

## 30. Frontend Setup

The frontend was created with the recommended Next.js defaults.

From project root:

```powershell
npx create-next-app@latest frontend
```

The generated configuration uses:

```text
TypeScript
ESLint
Tailwind CSS
App Router
No src/ directory
Cache Components
```

So frontend source lives under:

```text
frontend/app/
```

Install dependencies on a fresh clone:

```powershell
cd frontend
npm install
```

Start:

```powershell
npm run dev
```

Frontend:

```text
http://localhost:3000
```

---

## 31. Main Frontend Flow

Main page:

```text
frontend/app/page.tsx
```

Current modes:

```text
Record sale
Ask
```

### Record Sale Mode

```text
Record
  ↓
Stop
  ↓
Playback
  ↓
Transcribe recording
  ↓
Review sale
  ↓
Clarify if needed
  ↓
Confirm / Cancel
```

Browser APIs used:

```text
navigator.mediaDevices.getUserMedia
MediaRecorder
Blob
FormData
```

---

## 32. Recent Sales UI

Route:

```text
http://localhost:3000/sales
```

File:

```text
frontend/app/sales/page.tsx
```

Shows:

```text
customer
sale id
total
item count
payment status
date
```

---

## 33. Sale Details UI

Route:

```text
/sales/[saleId]
```

Files:

```text
frontend/app/sales/[saleId]/page.tsx
frontend/app/sales/[saleId]/sale-detail-client.tsx
```

Because Cache Components complained about runtime params, the dynamic page uses:

```tsx
export const instant = false;
```

The server page resolves the route parameter and passes it into a client component.

The page displays:

```text
customer name
sale total
sale/payment status
product names
quantities
unit price
line total
payments
inventory movements
financial summary
```

---

## 34. Intent Classifier

Supported intents currently include:

```text
CREATE_SALE
CHECK_INVENTORY
GET_CUSTOMER_INFO
GET_CUSTOMER_PURCHASE_HISTORY
GET_SALE_DETAILS
GET_TODAY_SALES
GET_EVENT_SALES
GET_REVENUE_SUMMARY
UNKNOWN
```

Architecture:

```text
deterministic pattern matching first
    ↓
LLM fallback only when needed
```

Examples:

```text
"ABC bought..."
→ CREATE_SALE
```

```text
"How many ceramic cup sets do I have left?"
→ CHECK_INVENTORY
```

```text
"What did ABC buy last time?"
→ GET_CUSTOMER_PURCHASE_HISTORY
```

---

## 35. Inventory Voice Query

Endpoint:

```text
POST /assistant/inventory?business_id=1
```

Example:

```json
{
  "text": "How many ceramic cup sets do I have left?"
}
```

Example response:

```json
{
  "product_id": 2,
  "product_name": "Ceramic Cup Set",
  "quantity_on_hand": 12,
  "found": true,
  "answer": "You have 12 Ceramic Cup Set in stock."
}
```

The quantity comes directly from PostgreSQL.

---

## 36. Validate Inventory in PostgreSQL

```sql
SELECT
    id,
    name,
    quantity_on_hand
FROM products
WHERE business_id = 1
  AND LOWER(name) = LOWER('Ceramic Cup Set');
```

Movement history:

```sql
SELECT
    id,
    product_id,
    sale_id,
    movement_type,
    quantity,
    created_at
FROM inventory_movements
WHERE product_id = 2
ORDER BY created_at DESC;
```

---

## 37. Ask Mode

The frontend can now record a question, transcribe it, classify intent, and answer inventory questions.

Example:

> “How many ceramic cup sets do I have left?”

Result:

```text
You have 12 Ceramic Cup Set in stock.
```

---

## 38. Customer Purchase History — Current Next Step

The next read-only capability being implemented is:

> “What did ABC buy last time?”

Planned endpoint:

```text
POST /assistant/customer-history?business_id=1
```

Flow:

```text
resolve customer
    ↓
query confirmed sales
    ↓
join sale_items + products
    ↓
return latest purchases
```

---

## 39. Start the Full App Locally

You need PostgreSQL, Ollama, backend and frontend available.

### Backend terminal

```powershell
cd C:\Users\sandh\VoiceInventoryApp\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

### Frontend terminal

```powershell
cd C:\Users\sandh\VoiceInventoryApp\frontend
npm run dev
```

### Check Ollama

```powershell
ollama list
```

Expected model:

```text
qwen3:4b
```

Useful URLs:

```text
Frontend:
http://localhost:3000

Recent Sales:
http://localhost:3000/sales

Swagger:
http://127.0.0.1:8000/docs
```

---

## 40. Fresh Machine Setup Summary

1. Install Git.
2. Install Python 3.11.
3. Install Node.js LTS.
4. Install PostgreSQL and pgAdmin.
5. Install Ollama.
6. Pull `qwen3:4b`.
7. Clone the repo.
8. Create PostgreSQL database.
9. Create backend `.env`.
10. Create Python venv.
11. Install `requirements.txt`.
12. Run `alembic upgrade head`.
13. Run `npm install` in frontend.
14. Start backend.
15. Start frontend.
16. Verify Ollama.
17. Open the frontend.

Commands:

```powershell
git clone https://github.com/Ishwinder-kaur/VoiceInventoryApp.git
cd VoiceInventoryApp\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
alembic upgrade head
python -m uvicorn app.main:app --reload
```

In another terminal:

```powershell
cd C:\Users\<user>\VoiceInventoryApp\frontend
npm install
npm run dev
```

Ollama:

```powershell
ollama pull qwen3:4b
ollama list
```

---

## 41. Useful PostgreSQL Queries

### Products

```sql
SELECT
    id,
    sku,
    name,
    unit_price,
    quantity_on_hand,
    currency,
    active
FROM products
ORDER BY id;
```

### Customers

```sql
SELECT
    id,
    business_id,
    name,
    phone,
    email
FROM customers
ORDER BY id;
```

### Sales

```sql
SELECT
    id,
    customer_id,
    sale_date,
    total,
    payment_status,
    status
FROM sales
ORDER BY id DESC;
```

### Sale Items

```sql
SELECT
    si.id,
    si.sale_id,
    p.name AS product_name,
    si.quantity,
    si.unit_price,
    si.line_total
FROM sale_items si
JOIN products p
    ON p.id = si.product_id
ORDER BY si.id DESC;
```

### Payments

```sql
SELECT
    id,
    sale_id,
    amount,
    currency,
    payment_method,
    payment_status,
    paid_at
FROM payments
ORDER BY id DESC;
```

### Inventory Movements

```sql
SELECT
    im.id,
    im.sale_id,
    p.name AS product_name,
    im.movement_type,
    im.quantity,
    im.created_at
FROM inventory_movements im
JOIN products p
    ON p.id = im.product_id
ORDER BY im.id DESC;
```

### Pending Voice Commands

```sql
SELECT
    id,
    business_id,
    status,
    original_text,
    created_at,
    confirmed_at
FROM pending_voice_commands
ORDER BY id DESC;
```

### Audit Events

```sql
SELECT
    id,
    business_id,
    entity_type,
    entity_id,
    action,
    actor_type,
    created_at
FROM audit_events
ORDER BY id DESC;
```

---

## 42. Git Workflow

Check changes:

```powershell
cd C:\Users\sandh\VoiceInventoryApp
git status
```

Stage:

```powershell
git add .
```

Review:

```powershell
git status
```

Ensure these are not staged:

```text
.env
backend/.venv
frontend/node_modules
frontend/.next
```

Commit:

```powershell
git commit -m "Build voice inventory sale flow, UI, history and assistant queries"
```

Push:

```powershell
git push origin master
```

---

## 43. Recommended `.gitignore`

```gitignore
# Python
backend/.venv/
__pycache__/
*.pyc

# Environment
.env
backend/.env
*.env

# Node
frontend/node_modules/
frontend/.next/

# IDE
.vscode/

# OS
.DS_Store
Thumbs.db
```

---

## 44. Why Next.js Instead of Streamlit?

Streamlit is excellent for:

```text
internal tools
dashboards
quick prototypes
data demos
```

This project is intended to become a real mobile-friendly transactional app.

Next.js gives better control over:

```text
microphone recording
mobile UX
PWA support
navigation
confirmation flows
authentication
production deployment
```

So the chosen architecture is:

```text
Next.js + FastAPI + PostgreSQL
```

rather than Streamlit.

---

## 45. Safety Principles

The application currently follows these rules:

```text
Never allow the LLM to execute arbitrary SQL.
Never create a sale before explicit user confirmation.
Do not rerun the LLM after a reviewed command is confirmed.
Resolve customers/products against PostgreSQL.
Use deterministic money calculations.
Revalidate inventory during sale creation.
Audit mutations.
Prefer deterministic business logic before LLM fallback.
```

---

## 46. End-to-End Sale Architecture

```text
Browser microphone
      ↓
MediaRecorder
      ↓
POST /voice/transcribe
      ↓
faster-whisper
      ↓
Transcript
      ↓
POST /voice/prepare
      ↓
Qwen structured extraction
      ↓
Payment normalization
      ↓
Customer/Product resolution
      ↓
Validation
      ↓
Missing/ambiguous?
   ↙             ↘
 YES              NO
  ↓                ↓
Clarification   Store pending command
  ↓                ↓
Resolve         Show confirmation
  ↓                ↓
Repeat          Owner confirms
                    ↓
             POST /voice/confirm
                    ↓
               create_sale()
                    ↓
             PostgreSQL transaction
              ↙     ↓      ↓      ↘
           Sale   Items  Payment  Inventory Movement
                    ↓
                  Audit
```

---

## 47. Read-Only Assistant Architecture

```text
Browser microphone
      ↓
Whisper
      ↓
Transcript
      ↓
Intent classifier
      ↓
Deterministic routing first
      ↓
LLM fallback when needed
      ↓
Read service
      ↓
PostgreSQL SELECT
      ↓
Answer
```

Current implemented query:

```text
CHECK_INVENTORY
```

Next:

```text
GET_CUSTOMER_PURCHASE_HISTORY
```

Later:

```text
GET_CUSTOMER_INFO
GET_TODAY_SALES
GET_REVENUE_SUMMARY
GET_EVENT_SALES
GET_SALE_DETAILS
```

---

## 48. AWS Deployment Target

Final target:

```text
Internet
   ↓
HTTPS / Load Balancer
   ↓
FastAPI on ECS
   ↓
RDS PostgreSQL
```

Container flow:

```text
Docker
  ↓
Amazon ECR
  ↓
Amazon ECS
```

Likely production architecture:

```text
Frontend
  ↓
Next.js deployment / CDN strategy
  ↓
FastAPI API
  ↓
ECS
  ↓
RDS PostgreSQL
```

Production items still to implement:

```text
Dockerfiles
docker-compose
environment-based API URLs
AWS Secrets Manager / Parameter Store
RDS
ECR
ECS task definitions
ECS services
ALB
HTTPS
domain
CloudWatch
health checks
production CORS
Alembic deployment strategy
authentication
authorization
backups
observability
rate limiting
AI inference provider decision
```

Local Ollama and local Whisper are development choices. Before production, decide whether inference will use:

```text
hosted APIs
AWS-hosted inference
separate GPU infrastructure
or dedicated model services
```

---

## 49. Configuration Changes Needed Before AWS

The frontend currently uses local URLs such as:

```text
http://127.0.0.1:8000
```

These should later use:

```env
NEXT_PUBLIC_API_URL=https://api.example.com
```

Backend should read production settings from environment variables:

```env
DATABASE_URL=...
OLLAMA_URL=...
MODEL_NAME=...
APP_ENV=production
ALLOWED_ORIGINS=...
```

---

## 50. Recommended Next Development Steps

1. Complete customer purchase history backend.
2. Connect customer history to Ask mode.
3. Add customer information query.
4. Add today's sales query.
5. Add revenue summary.
6. Add event/stall sales query.
7. Add sale lookup.
8. Improve voice clarification.
9. Add navigation/dashboard.
10. Add authentication.
11. Move API URLs to environment variables.
12. Dockerize frontend/backend.
13. Add docker-compose.
14. Validate clean-machine setup.
15. Prepare AWS infrastructure.
16. Migrate PostgreSQL to RDS.
17. Push images to ECR.
18. Deploy backend to ECS.
19. Deploy frontend.
20. Configure domain and HTTPS.
21. Add CloudWatch observability.
22. Production validation.

---

## 51. Troubleshooting Notes

### `py` is not recognized

Use:

```powershell
python
```

### PostgreSQL hostname error caused by password

URL-encode special characters in `DATABASE_URL`.

Example:

```text
@ -> %40
```

### Ollama `httpx.ReadTimeout`

Fixes used:

```text
think=false
keep_alive=30m
longer HTTP read timeout
warm the model manually
```

### Qwen misses payment phrase

Deterministic payment normalization handles common payment phrases.

### Product plural mismatch

Entity normalization handles simple pluralization such as:

```text
ceramic cup sets -> Ceramic Cup Set
```

### Next.js dynamic `useParams()` / blocking prerender issue

The dynamic sale page was changed to resolve route params in the server page, pass `saleId` to a client component, and use:

```tsx
export const instant = false;
```

---

## 52. Quick Daily Startup

Backend:

```powershell
cd C:\Users\sandh\VoiceInventoryApp\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd C:\Users\sandh\VoiceInventoryApp\frontend
npm run dev
```

Ollama check:

```powershell
ollama list
```

Open:

```text
Frontend:
http://localhost:3000

Recent Sales:
http://localhost:3000/sales

Swagger:
http://127.0.0.1:8000/docs
```

---

## 53. Current Project Status

Working locally:

- PostgreSQL connection
- Alembic migrations
- Business/customer/product APIs
- Alias support
- Sale creation
- Inventory decrement
- Payment creation
- Inventory movement ledger
- Audit events
- Recent sales API
- Sale details API
- Ollama Qwen extraction
- Deterministic payment normalization
- Customer/product entity resolution
- Pending confirmation sessions
- Clarification flow
- Deterministic clarification fast path
- Confirmation and cancellation
- Whisper transcription
- Browser microphone recording
- Sale review UI
- Clarification UI
- Confirm/cancel UI
- Recent sales UI
- Sale details UI
- Human-readable customer/product names
- Intent classifier
- Deterministic intent routing
- Inventory voice query
- Ask mode in frontend

Next:

- Customer purchase history query
- Connect customer history to Ask mode

Future:

- Customer information lookup
- Daily sales
- Revenue summaries
- Event/stall analytics
- Authentication
- Dockerization
- AWS ECS/RDS deployment
- Production AI inference architecture
