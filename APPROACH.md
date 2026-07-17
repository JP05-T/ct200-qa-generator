# APPROACH.md

## PDF Parsing

Started with PyMuPDF's `find_tables()` but it didn't work well with fpdf2-generated PDFs since there's no actual table markup — it's all just text blocks at different positions. So I went with extracting all spans and clustering them by x/y coordinates to figure out what's a table vs regular text.

For tables, I look at which spans share similar y-coordinates and have multiple x-position clusters. If a line has 2+ distinct x clusters, it's probably a table row. Then I group consecutive rows into table regions.

The tricky part was multi-line cells — like the E2 error row in the error codes table where "Motion artifact detected during measurement" wraps to a second line. The continuation detection checks if a row's first column doesn't match the expected pattern (like "E1", "E2" etc) and merges it into the previous row.

## Tree Building

Used a stack-based approach. When I hit a heading, I check its level by counting dots in the section number (e.g., "2.1.1.1" = level 4). Then I pop the stack until I find a parent at the right level and append the new heading there.

One thing I noticed — section 3.4 "Auto Shutoff" comes before 3.3 "Result Display" in the actual PDF even though numerically it should be after. I decided to preserve the document order rather than sort by section numbers, because that's what a tester would actually see when reading the manual.

## Table Cell Filtering

After detecting tables, I collect all the cell texts into a set and filter them out of the regular text blocks. Without this, you'd get duplicate content — the same text appearing as both a table node and a paragraph node.

## Content Hashing

Using SHA-256 truncated to 16 hex chars. Important thing — I normalize whitespace before hashing because fpdf2 outputs inconsistent spacing. Without normalization, re-ingesting the same PDF gives different hashes.

## Version Diff

Matching nodes between v1 and v2 by their title text. If two nodes in different versions have the same title, I compare their content hashes. If hashes differ, it's a modification. If a title exists in v2 but not v1, it's an addition, and vice versa.

This is simple but works for this assignment since the section titles don't change between versions. In a real system you'd probably want fuzzy matching.

## Staleness

I check staleness lazily — only when someone retrieves a generation, not when a new version is ingested. The generation stores the content hash of the node at generation time, and when you fetch it later, I compare against the current hash of that same node. If they differ, the test cases are stale.

## LLM Integration

Using Groq's Llama 3.1 8B model. The prompt asks for a JSON array of test cases with specific fields. After getting the response, I validate the JSON structure and filter out any test cases that don't have the required fields.

Also added a rule-based demo mode that works without an API key. It uses keyword matching on the section content to pick relevant test case templates (safety, measurement, error handling etc).

## Technology

- FastAPI + SQLAlchemy async + SQLite for the API layer
- PyMuPDF for PDF text extraction
- fpdf2 for generating the test PDFs (reportlab broke on Python 3.8)
- httpx for async LLM API calls
