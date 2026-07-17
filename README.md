# CT-200 Document Parser & QA Generator

 we have a blood pressure monitor called CardioTrack CT-200. It has a user manual as PDF. This project takes that PDF, breaks it into a tree structure (headings, paragraphs, tables, lists), and lets you browse through it via API.

Then when you upload a new version of the manual (like v2), it figures out what changed — which sections were added, removed, or modified.

The main thing is it can generate QA test cases from any section using an LLM. And if the document changes after test cases were made, it tells you those test cases are now stale.


API endpoints

Browse:
- `GET /api/documents` — list all versions
- `POST /api/documents/ingest` — ingest a new PDF
- `GET /api/versions/{id}/sections` — top level sections
- `GET /api/nodes/search?q=...` — search nodes
- `GET /api/nodes/{id}` — get a node with children
- `GET /api/versions/{v1}/diff/{v2}` — diff two versions

Selection:
- `POST /api/selections` — create a selection
- `GET /api/selections` — list all selections
- `GET /api/selections/{id}` — get selection details

Generation:
- `POST /api/generate` — generate test cases
- `GET /api/generations/{id}` — get test cases with staleness
- `GET /api/selections/{id}/generations` — list generations for a selection


 Database tables

- **DocumentVersion** — stores each PDF version (v1, v2, etc.)
- **DocumentNode** — every section/paragraph/table as a node with parent_id for tree structure, content_hash for staleness
- **Selection** — user picks nodes from a specific version
- **SelectionNode** — links selection to nodes
- **Generation** — stores generated test cases with hash at generation time, is_stale flag

Problems I ran into and fixed

- PDFs from fpdf2 have individual text spans, not actual table elements — so had to cluster x/y positions to detect tables
- "Error Codes" heading appears twice (section 4.2 and 7.1) — used section numbers to differentiate
- Section 3.4 appears before 3.3 in the PDF — kept document order instead of sorting by section number
- E2 error row text wraps to next line — added continuation detection based on first column pattern
- Numbered list items (1. Normal, 2. Elevated, etc.) were getting merged into one paragraph — added check before paragraph merging
- Content hashes were different for same text due to whitespace — added normalization

Staleness detection

1. User selects section from v1
2. Test cases generated → stored with content hash
3. v2 ingested → section content changes → new hash
4. User retrieves test cases → system compares hashes
5. Hashes different → is_stale = true → needs regeneration

 Tests

17 unit tests in `tests/test_parser.py` covering:
- Heading detection
- Duplicate headings as separate nodes
- Out of order sections
- Content hash normalization
- Table detection (specs, error codes, v2 with E6)
- Node types (headings, paragraphs, tables, numbered lists)

Tech used

- Python 3.8
- FastAPI (web framework)
- SQLAlchemy + SQLite (database)
- PyMuPDF (PDF reading)
- fpdf2 (PDF writing)
- httpx (HTTP calls to LLM)
- Groq API + Llama 3.1 8B (test case generation)
- pytest (testing)
