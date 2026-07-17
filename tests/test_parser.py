import pytest
import hashlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.parser import (
    parse_pdf, extract_heading_info, NUMBERED_ITEM,
    cluster_x_positions, detect_tables_from_spans
)
from app.models.models import compute_content_hash


class TestHeadingDetection:
    def test_section_number_heading(self):
        section, level = extract_heading_info("2.1 General Specifications")
        assert section == "2.1"
        assert level == 2

    def test_subsection_heading(self):
        section, level = extract_heading_info("2.1.1.1 Battery Life Under Typical Use")
        assert section == "2.1.1.1"
        assert level == 4

    def test_top_level_heading(self):
        section, level = extract_heading_info("1. Device Overview")
        assert section == "1"
        assert level == 1

    def test_non_heading_returns_zero(self):
        section, level = extract_heading_info("This is just regular body text")
        assert section == ""
        assert level == 0


class TestDuplicateHeadingParenting:
    def test_duplicate_heading_produces_separate_nodes(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())

        headings = [n for n in flat if n.node_type == "heading"]

        code_headings = [h for h in headings if "Error Codes" in h.title]
        assert len(code_headings) >= 2, (
            "Document has '4.2 Error Codes' and '7.1 Error Codes' - "
            "duplicate heading text must produce distinct nodes"
        )

        heading_42 = [h for h in code_headings if h.section_number == "4.2"]
        heading_71 = [h for h in code_headings if h.section_number == "7.1"]
        assert len(heading_42) == 1, "Should have exactly one 4.2 Error Codes"
        assert len(heading_71) == 1, "Should have exactly one 7.1 Error Codes"

    def test_heading_parent_is_correct_section(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())

        headings = {n.section_number: n for n in flat if n.section_number}

        assert "1.1" in headings
        assert "1.2" in headings
        assert "2.1" in headings
        assert "4.2" in headings
        assert "8.1" in headings


class TestOutofOrderSections:
    def test_sections_preserve_document_order(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())

        headings = [n for n in flat if n.node_type == "heading" and n.section_number]
        section_nums = [h.section_number for h in headings]

        assert "3.4" in section_nums, "3.4 Auto Shutoff exists in document"
        assert "3.3" in section_nums, "3.3 Result Display exists in document"
        idx_34 = section_nums.index("3.4")
        idx_33 = section_nums.index("3.3")
        assert idx_34 < idx_33, (
            "3.4 appears before 3.3 in the PDF (out-of-order numbering) - "
            "parser must preserve document order, not sort by section number"
        )


class TestContentHash:
    def test_same_text_same_hash(self):
        h1 = compute_content_hash("Hello world")
        h2 = compute_content_hash("Hello world")
        assert h1 == h2

    def test_different_text_different_hash(self):
        h1 = compute_content_hash("Hello world")
        h2 = compute_content_hash("Goodbye world")
        assert h1 != h2

    def test_whitespace_normalization(self):
        h1 = compute_content_hash("  Hello   world  ")
        h2 = compute_content_hash("Hello world")
        assert h1 == h2


class TestTableDetection:
    def test_specs_table_detected(self):
        tree, tables = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        spec_tables = [t for t in tables if t["page"] == 1]
        assert len(spec_tables) >= 1, "Should detect General Specifications table on page 1"
        table = spec_tables[0]
        assert len(table["headers"]) == 2, "Specs table has 2 columns"
        assert len(table["rows"]) == 7, "Specs table has 7 data rows"

    def test_error_codes_table_detected(self):
        tree, tables = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        error_tables = [t for t in tables if t["page"] == 2]
        assert len(error_tables) >= 1, "Should detect Error Codes table on page 2"
        table = error_tables[0]
        assert len(table["headers"]) == 3, "Error table has 3 columns"
        assert len(table["rows"]) == 5, "Error table has 5 data rows (E1-E5)"

    def test_v2_error_table_has_e6(self):
        tree, tables = parse_pdf("data/v2-CardioTrack_CT200_Manual.pdf")
        error_tables = [t for t in tables if t["page"] == 2]
        assert len(error_tables) >= 1
        table = error_tables[0]
        assert len(table["rows"]) == 6, "v2 Error table has 6 data rows (E1-E6)"


class TestNodeTypes:
    def test_tree_has_headings(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())
        headings = [n for n in flat if n.node_type == "heading"]
        assert len(headings) >= 15, f"Expected >=15 headings, got {len(headings)}"

    def test_tree_has_paragraphs(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())
        paragraphs = [n for n in flat if n.node_type == "paragraph"]
        assert len(paragraphs) >= 10, f"Expected >=10 paragraphs, got {len(paragraphs)}"

    def test_tree_has_tables(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())
        tables = [n for n in flat if n.node_type == "table"]
        assert len(tables) >= 2, f"Expected >=2 tables, got {len(tables)}"

    def test_tree_has_numbered_list(self):
        tree, _ = parse_pdf("data/v1-CardioTrack_CT200_Manual.pdf")
        flat = []
        for node in tree:
            flat.extend(node.flatten())
        lists = [n for n in flat if n.node_type == "numbered_list"]
        assert len(lists) >= 1, "Expected at least 1 numbered list (BP classification)"
