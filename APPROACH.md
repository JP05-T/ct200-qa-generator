# APPROACH.md

## PDF Parsing

Started with PyMuPDF's `find_tables()` but it didn't work since fpdf2 PDFs have no table markup — just text at different positions. So I extract all text spans and cluster them by x/y coordinates. If a line has spans at 2+ different x positions, it's probably a table row.

For multi-line cells (like E2 error row wrapping to next line), I check if the first column doesn't match the expected pattern and merge it into the previous row.

## Tree Building

Section numbers tell the hierarchy — "2.1.1.1" means level 4. I use a stack to track parents. When I hit a heading, I pop the stack until I find the right parent level.

Section 3.4 appears before 3.3 in the actual PDF. I kept document order instead of sorting by number because that's what a tester would see.

After detecting tables, I collect all cell texts and filter them from regular text blocks so the same content doesn't appear twice.

## Content Hashing

SHA-256 truncated to 16 chars. Normalized whitespace before hashing because fpdf2 generates inconsistent spacing — without this, re-ingesting the same PDF gives different hashes.

## Version Diff

Match nodes by title between v1 and v2. Same title + different hash = modified. Title in v2 but not v1 = added. Simple but works since section titles don't change between versions.

## Staleness

Check lazily — only when someone retrieves test cases, not when new version is ingested. The generation stores the hash when test cases were made. On retrieval, compare against current hash. Different = stale.

## LLM

Groq API with Llama 3.1 8B. Prompt asks for JSON array of test cases. Validate the response and filter invalid ones. Added a demo mode using keyword matching so it works without API key.
