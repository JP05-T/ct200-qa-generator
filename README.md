# CT-200 Document Parser & QA Generator

Backend API system for parsing medical device manuals into structured trees, detecting version changes, and generating QA test cases via LLM.

## Quick Start

```bash
pip install -r requirements.txt

# Generate test PDFs
python data/generate_pdfs.py

# Start server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Run tests
python -m pytest tests/ -v

# Run demo
python demo.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List all ingested document versions |
| POST | `/api/documents/ingest` | Ingest a new PDF version |
| GET | `/api/versions/{id}/sections` | List top-level sections for a version |
| GET | `/api/nodes/search?q=...` | Full-text search across all nodes |
| GET | `/api/nodes/{id}` | Get a node and its children |
| GET | `/api/versions/{v1}/diff/{v2}` | Compare two versions |
| POST | `/api/selections` | Create a version-pinned node selection |
| GET | `/api/selections` | List all selections |
| POST | `/api/generate` | Generate QA test cases (requires LLM key) |
| GET | `/api/generations/{id}` | Get test cases with staleness check |

## LLM Configuration

Test case generation requires an LLM API key. Set environment variables:

```bash
# Copy and fill in your key
cp .env.example .env

# Groq (free tier available)
LLM_API_KEY=gsk_your_key_here
LLM_API_URL=https://api.groq.com/openai/v1/chat/completions
LLM_MODEL=llama-3.1-8b-instant
```

Without an LLM key, all other features (ingest, browse, diff, selection, staleness) work fully.

## Project Structure

```
app/
  main.py              # FastAPI app entry point
  models/
    database.py        # SQLAlchemy async engine + SQLite
    models.py          # ORM models + content hash
    schemas.py         # Pydantic request/response schemas
  services/
    parser.py          # PDF parsing with span clustering
    versioning.py      # Ingest, diff, staleness detection
    llm.py             # LLM integration + JSON validation
  routers/
    documents.py       # Browse API (ingest, sections, search, diff)
    selections.py      # Selection API (create, list, get)
    generation.py      # Generation API (generate, retrieve)
data/
  generate_pdfs.py     # Creates v1/v2 test PDFs
  v1-CardioTrack_CT200_Manual.pdf
  v2-CardioTrack_CT200_Manual.pdf
tests/
  test_parser.py       # 17 unit tests
demo.py                # End-to-end demo script
```

## Key Design Decisions

- **Parser handles 5 irregularities**: duplicate headings, out-of-order sections, multi-line table cells, numbered lists in body text, section numbers with inconsistent formats
- **Staleness is lazy**: checked at retrieval time by comparing content hashes
- **Version diff uses title-based matching**: pragmatic for documents with stable section titles
- **All generated PDFs are in-repo**: no external PDF source files needed

See [APPROACH.md](APPROACH.md) for detailed design rationale.
