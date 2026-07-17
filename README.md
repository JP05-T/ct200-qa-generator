# CT-200 Document Parser & QA Generator

A backend system that parses medical device manuals (PDF) into structured, browsable trees, tracks document versions, detects changes between them, and generates QA test cases using AI.

Built for the Tri9T AI Engineering Internship Assignment.

---

## Problem Statement

Medical device documentation changes frequently. When a manual is updated (new error codes, changed specs, added sections), QA testers need to know which test cases are now outdated. This project automates:

1. Parsing unstructured PDF manuals into structured data
2. Detecting what changed between document versions
3. Generating test cases from selected sections via LLM
4. Flagging test cases that became stale after document updates

---

## How It Works

```
PDF Manual v1  ──→  Parse into Tree  ──→  Store in DB
                         │
                    Browse / Search
                         │
                    Select Section
                         │
                    Generate Test Cases (LLM)
                         │
PDF Manual v2  ──→  Parse & Diff  ──→  Detect Staleness
```

---

## Setup & Running

### Prerequisites
- Python 3.8+
- pip

### Installation
```bash
git clone https://github.com/JP05-T/ct200-qa-generator.git
cd ct200-qa-generator
pip install -r requirements.txt
```

### Generate Test PDFs
```bash
python data/generate_pdfs.py
```
Creates `data/v1-CardioTrack_CT200_Manual.pdf` and `data/v2-CardioTrack_CT200_Manual.pdf`

### Start Server
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API docs available at: `http://127.0.0.1:8000/docs`

### Run Tests
```bash
python -m pytest tests/ -v
```
17 unit tests covering parser irregularities, table detection, content hashing, and tree structure.

### Run Demo
```bash
python demo.py
```
End-to-end walkthrough: ingest v1 → browse → search → ingest v2 → diff → select → generate test cases.

---

## API Reference

### Browse

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List all ingested document versions |
| POST | `/api/documents/ingest?pdf_path=...&description=...` | Ingest a new PDF version |
| GET | `/api/versions/{id}/sections` | List top-level sections for a version |
| GET | `/api/nodes/search?q=...` | Full-text search across all nodes |
| GET | `/api/nodes/{id}` | Get a node with its children |
| GET | `/api/versions/{v1}/diff/{v2}` | Compare two versions |

### Selection

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/selections` | Create a version-pinned node selection |
| GET | `/api/selections` | List all selections |
| GET | `/api/selections/{id}` | Get selection with node details |

### Generation & Retrieval

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Generate QA test cases for a selection |
| GET | `/api/generations/{id}` | Get test cases with staleness check |
| GET | `/api/selections/{id}/generations` | List all generations for a selection |

---

## LLM Configuration

Test case generation works in two modes:

### Demo Mode (no API key needed)
Uses rule-based keyword matching to generate test cases. Automatically activates when `LLM_API_KEY` is not set.

### Live Mode (Groq API)
```bash
cp .env.example .env
# Edit .env and add your Groq API key
```

Get a free key at: https://console.groq.com/keys

---

## Project Structure

```
app/
  main.py                    FastAPI entry point, router registration
  models/
    database.py              SQLAlchemy async engine + SQLite setup
    models.py                ORM models (DocumentVersion, DocumentNode,
                             Selection, SelectionNode, Generation)
    schemas.py               Pydantic request/response schemas
  services/
    parser.py                PDF parsing: span extraction, table detection,
                             tree construction
    versioning.py            Ingest, version diff, staleness detection
    llm.py                   LLM integration, prompt design, JSON validation,
                             demo mode fallback
  routers/
    documents.py             Browse API endpoints
    selections.py            Selection API endpoints
    generation.py            Generation + retrieval API endpoints
data/
  generate_pdfs.py           Script to create v1/v2 test PDFs
  v1-CardioTrack_CT200_Manual.pdf
  v2-CardioTrack_CT200_Manual.pdf
tests/
  test_parser.py             17 unit tests
demo.py                      End-to-end demo script
requirements.txt             Python dependencies
README.md
APPROACH.md                  Design decisions and trade-offs
.env.example                 Environment variable template
```

---

## Database Schema

```
DocumentVersion
  ├── id, version_number, source_file, description, created_at
  └── has many DocumentNodes

DocumentNode
  ├── id, version_id, parent_id (self-referencing FK)
  ├── node_type (heading/paragraph/table/numbered_list/section)
  ├── title, section_number, heading_level, body_text
  ├── content_hash (SHA-256 truncated, for staleness detection)
  └── page_number

Selection
  ├── id, name, version_id
  └── has many SelectionNodes (links to DocumentNodes)

Generation
  ├── id, selection_id, node_id, node_version_id
  ├── content_hash_at_generation (hash when test cases were created)
  ├── test_cases (JSON), model_used
  └── is_stale (updated on retrieval via hash comparison)
```

---

## Parser Irregularities Handled

| Irregularity | Example | How it's handled |
|-------------|---------|-----------------|
| Duplicate headings | "4.2 Error Codes" and "7.1 Error Codes" | Section numbers used as unique identifiers |
| Out-of-order sections | 3.4 appears before 3.3 in PDF | Document order preserved, not sorted by number |
| Multi-line table cells | E2 error row split across 2 lines | Y-coordinate based continuation detection |
| Numbered lists in body text | "1. Normal: systolic < 120..." | Regex detection prevents paragraph merging |
| Inconsistent heading formats | "1. Title" vs "2.1 Title" | Flexible regex handles both patterns |

---

## Staleness Detection Flow

```
1. User selects section from v1
2. User generates test cases → stored with content_hash_at_generation
3. v2 is ingested → node content changes → new content_hash
4. User retrieves test cases → system compares hashes
5. If hashes differ → is_stale = true → test cases need regeneration
```

---

## Test Coverage

17 unit tests in `tests/test_parser.py`:

- Heading detection (section numbers, subsections, non-headings)
- Duplicate heading produces separate tree nodes
- Out-of-order sections preserved in document order
- Content hash with whitespace normalization
- Table detection (specs table, error codes table, v2 with E6)
- Node types (headings, paragraphs, tables, numbered lists)

---

## Tech Stack

- **Python 3.8** — language
- **FastAPI** — async web framework
- **SQLAlchemy + aiosqlite** — async ORM with SQLite
- **PyMuPDF (fitz)** — PDF text extraction
- **fpdf2** — PDF generation (test documents)
- **httpx** — async HTTP client for LLM API
- **Groq API / Llama 3.1 8B** — LLM for test case generation
- **pytest** — testing framework
