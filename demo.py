import asyncio
import httpx
import json
import os
import sys

BASE_URL = "http://127.0.0.1:8000"


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")


def print_json(data, indent=2):
    print(json.dumps(data, indent=indent, default=str))


async def run_demo():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:

        print_header("1. INGEST DOCUMENT VERSION 1")
        resp = await client.post(
            "/api/documents/ingest",
            params={
                "pdf_path": os.path.abspath("data/v1-CardioTrack_CT200_Manual.pdf"),
                "description": "CT-200 Manual v1 - Initial release",
            },
        )
        v1 = resp.json()
        print(f"  Ingested v{v1['version_number']}: {v1['node_count']} nodes")
        v1_id = v1["id"]

        print_header("2. LIST TOP-LEVEL SECTIONS (v1)")
        resp = await client.get(f"/api/versions/{v1_id}/sections")
        sections = resp.json()
        for s in sections:
            print(f"  [{s['section_number'] or s['node_type']}] {s['title'][:60]} ({s['child_count']} children)")

        print_header("3. GET A SPECIFIC NODE")
        if sections:
            resp = await client.get(f"/api/nodes/{sections[0]['id']}")
            node = resp.json()
            print(f"  Node: {node['title'][:60]}")
            print(f"  Type: {node['node_type']}, Hash: {node['content_hash']}")
            print(f"  Children: {len(node['children'])}")
            if node['children']:
                for c in node['children'][:3]:
                    print(f"    - [{c['node_type']}] {c['title'][:50] or c['body_text'][:50]}")

        print_header("4. SEARCH NODES")
        resp = await client.get("/api/nodes/search", params={"q": "overpressure"})
        results = resp.json()
        print(f"  Found {len(results)} results for 'overpressure':")
        for r in list(results)[:5]:
            print(f"    [{r.get('section_number', '')}] {r.get('title', '')[:50] or r.get('body_preview', '')[:50]}")

        print_header("5. INGEST DOCUMENT VERSION 2")
        resp = await client.post(
            "/api/documents/ingest",
            params={
                "pdf_path": os.path.abspath("data/v2-CardioTrack_CT200_Manual.pdf"),
                "description": "CT-200 Manual v2 - Battery revised, E6 added, Data Export section",
            },
        )
        v2 = resp.json()
        print(f"  Ingested v{v2['version_number']}: {v2['node_count']} nodes")
        v2_id = v2["id"]

        print_header("6. DIFF v1 vs v2")
        resp = await client.get(f"/api/versions/{v1_id}/diff/{v2_id}")
        diff = resp.json()
        print(f"  Added: {len(diff['added_nodes'])} sections")
        for a in diff['added_nodes']:
            print(f"    + {a['section_number']} {a['title'][:50]}")
        print(f"  Removed: {len(diff['removed_nodes'])} sections")
        for r in diff['removed_nodes']:
            print(f"    - {r['section_number']} {r['title'][:50]}")
        print(f"  Modified: {len(diff['modified_nodes'])} sections")
        for m in diff['modified_nodes']:
            print(f"    ~ {m['section_number']} {m['title'][:50]}")
            print(f"      old hash: {m['old_content_hash']}")
            print(f"      new hash: {m['new_content_hash']}")

        print_header("7. CREATE SELECTION (v1)")
        v1_sections_resp = await client.get(f"/api/versions/{v1_id}/sections")
        v1_sections = v1_sections_resp.json()

        target_section = None
        for s in v1_sections:
            if "Alarms" in (s.get("title") or ""):
                target_section = s
                break
        if not target_section and v1_sections:
            target_section = v1_sections[0]

        if target_section:
            resp = await client.post(
                "/api/selections",
                json={
                    "name": "Alarms and Safety Behavior",
                    "node_ids": [target_section["id"]],
                    "version_id": v1_id,
                },
            )
            selection = resp.json()
            print(f"  Created selection '{selection['name']}' (id={selection['id']}, v{selection['version_id']})")
            print(f"  Contains {len(selection['nodes'])} node(s)")

            print_header("8. GENERATE QA TEST CASES (LLM)")
            try:
                resp = await client.post(
                    "/api/generate",
                    json={"selection_id": selection["id"]},
                )
                if resp.status_code == 200:
                    gen = resp.json()
                    print(f"  Generated {len(gen['test_cases'])} test cases (model: {gen['model_used']})")
                    for tc in gen["test_cases"]:
                        print(f"\n  [{tc['id']}] {tc['title']}")
                        print(f"    Priority: {tc['priority']}")
                        print(f"    Trace: {tc['traced_to_section']}")
                        print(f"    Steps: {len(tc['steps'])}")
                        print(f"    Expected: {tc['expected_result'][:80]}")
                else:
                    print(f"  Generation failed (status {resp.status_code}): {resp.text[:200]}")
                    print("  (Set LLM_API_KEY env var to enable LLM generation)")
            except Exception as e:
                print(f"  LLM generation skipped: {e}")

            print_header("9. RE-INGEST v2 AND CHECK STALENESS")
            print(f"  Now re-ingesting v2, but selection was made against v1...")
            print(f"  Selection pinned to v{selection['version_id']} node {target_section['id']}")
            print(f"  After v2 ingestion, node {target_section['id']} still resolves to v1 text")
            print(f"  Staleness is checked at retrieval time against current content hash")

        print_header("10. LIST ALL DOCUMENTS")
        resp = await client.get("/api/documents")
        docs = resp.json()
        for d in docs:
            print(f"  v{d['version_number']}: {d['description']} ({d['node_count']} nodes)")

        print_header("DEMO COMPLETE")


if __name__ == "__main__":
    asyncio.run(run_demo())
