# 📄 PDF RAG Backend

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-REST_Framework-092E20?style=for-the-badge&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-Async_Tasks-37814A?style=for-the-badge&logo=celery&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Message_Broker-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-AI_Orchestration-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white)

**A production-ready backend for Retrieval-Augmented Generation (RAG) over PDF documents.**  
Upload documents, auto-index them, and chat with your data through an AI-powered API.

</div>

---

## 🧠 What Is This?

This project is a fully containerized **RAG (Retrieval-Augmented Generation)** backend that allows you to:

- Upload PDF documents via Django Admin
- Automatically chunk and embed them in the background using **Celery + Redis**
- Store vector embeddings in **PostgreSQL with pgvector**
- Ask natural language questions and receive AI-generated answers grounded in your documents — with **source attribution** down to the exact page

No hallucinations from general knowledge. Every answer is derived from the documents you provide.

---

## ⚙️ Architecture

```
User uploads PDF via Django Admin
         │
         ▼
  Django post_save Signal
  (fires immediately, non-blocking)
         │
         ▼
   Celery Worker (via Redis)
         │
    ┌────┴─────────────────────────────┐
    │  1. Parse PDF pages              │
    │  2. Split into chunks            │
    │     (RecursiveCharacterTextSplitter │
    │      chunk=1000, overlap=200)    │
    │  3. Embed via OpenRouter API     │
    │     (text-embedding-3-small)     │
    │  4. Store in PostgreSQL          │
    │     (pgvector extension)         │
    └──────────────────────────────────┘
         │
         ▼
  POST /api/chat/ask/
         │
    ┌────┴──────────────────────────────────────┐
    │  1. Embed the user's question             │
    │  2. L2Distance search via Django ORM      │
    │     (pgvector.django)                     │
    │  3. Retrieve top-k relevant chunks        │
    │  4. Send context + question to LLM        │
    │     (meta-llama/llama-3-8b-instruct:free) │
    │  5. Return answer + sources               │
    └───────────────────────────────────────────┘
```

### Key Architectural Decisions

**Async Pipeline via Django Signals + Celery**
PDF processing is heavy — parsing, chunking, and embedding hundreds of pages can take seconds or minutes. By wiring a `post_save` signal to a Celery task, document ingestion happens entirely off the request/response cycle. The API responds instantly; the worker handles the rest.

**Vector Search through Django ORM**
Semantic similarity search is performed directly via `pgvector.django` using `L2Distance` (Euclidean distance) — no separate vector database needed. PostgreSQL handles both relational data and vector search in a single query.

**Smart Chunking with Overlap**
Using `RecursiveCharacterTextSplitter` (chunk size: 1000 chars, overlap: 200 chars) ensures that sentences split across chunk boundaries don't lose context. This meaningfully improves retrieval quality.

**Modular Django App Structure**
Django applications are organized under a custom `apps/` directory:

```
apps/
├── documents/   # PDF upload, chunking, embedding pipeline
└── chat/        # Question answering, vector search, LLM calls
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | Django 4.x + Django REST Framework |
| **Language** | Python 3.11 |
| **Async Tasks** | Celery |
| **Message Broker** | Redis |
| **Database** | PostgreSQL + pgvector |
| **AI Orchestration** | LangChain |
| **Embeddings Model** | `openai/text-embedding-3-small` via OpenRouter |
| **LLM** | `meta-llama/llama-3-8b-instruct:free` via OpenRouter |
| **Containerization** | Docker + Docker Compose |

---

## 🚀 Quick Start

The entire stack — Django, Celery, Redis, and PostgreSQL — runs in Docker. Three commands and you're up.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed
- An [OpenRouter](https://openrouter.ai/) API key (free tier works)

### 1. Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set your API key:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

All sensitive credentials (database passwords, API keys) are kept out of version control via `.env`.

### 3. Build and run

```bash
docker-compose up --build
```

This will start:
- `web` — Django application on `http://localhost:8000`
- `celery` — Async worker for PDF processing
- `redis` — Message broker
- `db` — PostgreSQL with pgvector

### 4. Enable the pgvector extension

Once the database is running, connect to it and enable the vector extension:

```bash
docker-compose exec db psql -U postgres -d your_db_name
```

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Run migrations

```bash
docker-compose exec web python manage.py migrate
```

### 6. Create a superuser

```bash
docker-compose exec web python manage.py createsuperuser
```

Then go to [http://localhost:8000/admin](http://localhost:8000/admin) and upload your first PDF document. The Celery worker will pick it up automatically and begin indexing.

---

## 📡 API Reference

### `POST /api/chat/ask/`

Ask a natural language question against all indexed documents.

**Request**

```http
POST /api/chat/ask/
Content-Type: application/json

{
  "question": "What are the key findings in the Q3 report?"
}
```

**Response**

```json
{
  "answer": "The Q3 report highlights a 14% increase in revenue driven by...",
  "sources": [
    {
      "chunk_id": 42,
      "document": "Q3_Financial_Report_2024.pdf",
      "page": 7
    },
    {
      "chunk_id": 43,
      "document": "Q3_Financial_Report_2024.pdf",
      "page": 8
    }
  ]
}
```

Every answer includes a `sources` array so you can trace exactly which document and page the information came from.

---

## 🗂️ Project Structure

```
.
├── apps/
│   ├── documents/          # PDF upload, chunking, embedding
│   │   ├── models.py       # Document & Chunk models
│   │   ├── signals.py      # post_save → Celery dispatch
│   │   └── tasks.py        # PDF processing Celery task
│   └── chat/               # Q&A pipeline
│       ├── views.py        # /api/chat/ask/ endpoint
│       └── services.py     # Vector search + LLM call
├── config/
│   ├── settings.py
│   ├── celery.py
│   └── urls.py
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── requirements.txt
```

---

## 🔮 Future Improvements

- **Conversation Memory** — Maintain chat history per session using LangChain's `ConversationBufferMemory` so the LLM can answer follow-up questions with full context.
- **Frontend UI** — A React or Next.js interface for uploading documents and chatting, removing the dependency on Django Admin for end users.
- **Hybrid Search** — Combine pgvector semantic search with PostgreSQL full-text search (BM25) for improved retrieval on keyword-heavy queries.
- **Document Management API** — REST endpoints to list, delete, and re-index documents programmatically.
- **Authentication** — JWT-based auth (via `djangorestframework-simplejwt`) to support multi-user deployments with per-user document isolation.
- **Streaming Responses** — Stream LLM output token-by-token using Server-Sent Events for a more responsive chat experience.

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
