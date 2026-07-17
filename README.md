# CT-200 Document Parser & QA Generator

## What it does
Takes PDF manuals for a fictional blood pressure monitor (CardioTrack CT-200), parses them into structured trees, tracks versions, and generates QA test cases from selected sections.

## How to run
```bash
pip install -r requirements.txt
python data/generate_pdfs.py
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Tests: `python -m pytest tests/ -v`
Demo: `python demo.py`

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/documents` | List all versions |
| POST | `/api/documents/ingest` | Ingest new PDF |
| GET | `/api/versions/{id}/sections` | Top-level sections |
| GET | `/api/nodes/search?q=...` | Search nodes |
| GET | `/api/nodes/{id}` | Get node + children |
| GET | `/api/versions/{v1}/diff/{v2}` | Diff two versions |
| POST | `/api/selections` | Create selection |
| GET | `/api/selections` | List selections |
| POST | `/api/generate` | Generate test cases |
| GET | `/api/generations/{id}` | Get test cases + staleness |

## LLM Setup (optional)
Works without it — demo mode generates sample test cases. For real LLM:
```bash
cp .env.example .env
# edit .env with your Groq API key
```

## Project structure
```
app/
  main.py
  models/     - database.py, models.py, schemas.py
  services/   - parser.py, versioning.py, llm.py
  routers/    - documents.py, selections.py, generation.py
data/         - PDFs + generation script
tests/        - test_parser.py (17 tests)
demo.py       - end-to-end demo
```

## Problems solved
- Duplicate section headings (4.2 and 7.1 both called "Error Codes")
- Out of order sections (3.4 appears before 3.3 in the PDF)
- Multi-line table cells (E2 error row split across 2 lines)
- Numbered lists in body text getting merged into one blob
- Staleness detection when document gets updated
