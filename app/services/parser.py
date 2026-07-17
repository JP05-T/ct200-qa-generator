import re
import fitz
from typing import List, Dict, Any, Optional, Tuple


HEADING_PATTERN = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(.+)$")
NUMBERED_ITEM = re.compile(r"^(\d+)\.\s+(.+)$")
PAGE_FOOTER = re.compile(r"^Page\s+\d+/\d+$", re.IGNORECASE)


class ParsedElement:
    def __init__(self, element_type: str, text: str, page: int,
                 font_size: float = 10.0, is_bold: bool = False,
                 bbox: list = None, heading_level: int = 0,
                 section_number: str = ""):
        self.element_type = element_type
        self.text = text
        self.page = page
        self.font_size = font_size
        self.is_bold = is_bold
        self.bbox = bbox or []
        self.heading_level = heading_level
        self.section_number = section_number


class TreeNode:
    def __init__(self, node_type: str, title: str = "", body_text: str = "",
                 section_number: str = "", heading_level: int = 0,
                 page_number: int = 0, node_id: str = ""):
        self.node_type = node_type
        self.title = title
        self.body_text = body_text
        self.section_number = section_number
        self.heading_level = heading_level
        self.page_number = page_number
        self.node_id = node_id
        self.children: List["TreeNode"] = []

    def flatten(self) -> List["TreeNode"]:
        result = [self]
        for child in self.children:
            result.extend(child.flatten())
        return result


def extract_heading_info(text: str) -> Tuple[str, int]:
    m = HEADING_PATTERN.match(text.strip())
    if m:
        section_num = m.group(1)
        dots = section_num.count(".")
        level = dots + 1
        return section_num, level
    return "", 0


def is_page_footer(text: str, bbox: list, page_height: float) -> bool:
    if PAGE_FOOTER.match(text.strip()):
        return True
    if bbox and bbox[1] > page_height - 40 and text.strip().startswith("Page "):
        return True
    return False


def cluster_x_positions(x_positions: List[float], gap: float = 30) -> List[List[float]]:
    if not x_positions:
        return []
    sorted_x = sorted(set(x_positions))
    clusters = [[sorted_x[0]]]
    for x in sorted_x[1:]:
        if x - clusters[-1][-1] < gap:
            clusters[-1].append(x)
        else:
            clusters.append([x])
    return clusters


def detect_tables_from_spans(page: fitz.Page, page_num: int) -> List[Dict]:
    blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
    all_spans = []
    for b in blocks:
        if b["type"] == 0:
            for line in b["lines"]:
                for span in line["spans"]:
                    all_spans.append({
                        "text": span["text"],
                        "bbox": list(span["bbox"]),
                        "line_y": line["bbox"][1],
                    })

    if not all_spans:
        return []

    lines_by_y = {}
    for s in all_spans:
        y_key = round(s["line_y"], 0)
        if y_key not in lines_by_y:
            lines_by_y[y_key] = []
        lines_by_y[y_key].append(s)

    sorted_ys = sorted(lines_by_y.keys())

    table_row_ys = []
    for y in sorted_ys:
        line_spans = lines_by_y[y]
        if len(line_spans) >= 2:
            x_positions = [s["bbox"][0] for s in line_spans]
            clusters = cluster_x_positions(x_positions)
            if len(clusters) >= 2:
                table_row_ys.append(y)

    if len(table_row_ys) < 2:
        return []

    table_regions = []
    current_region = [table_row_ys[0]]
    for i in range(1, len(table_row_ys)):
        gap_val = table_row_ys[i] - table_row_ys[i - 1]
        if gap_val < 40:
            current_region.append(table_row_ys[i])
        else:
            if len(current_region) >= 2:
                table_regions.append(current_region)
            current_region = [table_row_ys[i]]
    if len(current_region) >= 2:
        table_regions.append(current_region)

    tables = []
    for region_ys in table_regions:
        rows_by_y = {}
        for y in region_ys:
            for s in lines_by_y[y]:
                y_key = round(s["line_y"], 0)
                if y_key not in rows_by_y:
                    rows_by_y[y_key] = []
                rows_by_y[y_key].append(s)

        sorted_row_ys = sorted(rows_by_y.keys())
        if len(sorted_row_ys) < 2:
            continue

        max_spans = max(len(rows_by_y[y]) for y in sorted_row_ys)
        num_cols = max_spans

        table_rows = []
        for y in sorted_row_ys:
            row_spans = sorted(rows_by_y[y], key=lambda s: s["bbox"][0])
            cells = [""] * num_cols
            for si, s in enumerate(row_spans):
                col_idx = min(si, num_cols - 1)
                if cells[col_idx]:
                    cells[col_idx] += " " + s["text"]
                else:
                    cells[col_idx] = s["text"]
            table_rows.append(cells)

        continuation_rows = set()
        first_col_pattern = None
        sample_first_cols = [r[0].strip() for r in table_rows if r[0].strip()]
        if sample_first_cols:
            e_pattern_matches = sum(1 for fc in sample_first_cols if re.match(r"^E\d+$", fc))
            alpha_matches = sum(1 for fc in sample_first_cols if re.match(r"^[A-Z]", fc))
            if e_pattern_matches > len(sample_first_cols) / 2:
                first_col_pattern = r"^E\d+$"
            elif alpha_matches > len(sample_first_cols) / 2:
                first_col_pattern = r"^[A-Z]"

        for i in range(1, len(table_rows)):
            prev = table_rows[i - 1]
            curr = table_rows[i]
            has_content = any(c.strip() for c in curr)
            if not has_content:
                continue
            curr_first = curr[0].strip()
            is_continuation = False
            if first_col_pattern and curr_first and not re.match(first_col_pattern, curr_first):
                is_continuation = True
            if not is_continuation and curr_first == "" and any(c.strip() for c in curr[1:]):
                is_continuation = True
            if is_continuation:
                for pi in range(min(len(prev), len(curr))):
                    if prev[pi].strip() and curr[pi].strip():
                        prev[pi] = prev[pi] + " " + curr[pi]
                    elif curr[pi].strip():
                        prev[pi] = curr[pi]
                if len(curr) > len(prev):
                    for pi in range(len(prev), len(curr)):
                        if curr[pi].strip():
                            prev.append(curr[pi])
                continuation_rows.add(i)

        filtered_rows = [
            table_rows[i] for i in range(len(table_rows))
            if i not in continuation_rows
        ]

        if len(filtered_rows) >= 2:
            tables.append({
                "page": page_num + 1,
                "headers": filtered_rows[0],
                "rows": filtered_rows[1:],
                "table_y": sorted_row_ys[0],
            })

    return tables


def parse_pdf(pdf_path: str) -> Tuple[List[TreeNode], List[Dict]]:
    doc = fitz.open(pdf_path)
    all_tables = []

    for pn in range(len(doc)):
        tables = detect_tables_from_spans(doc[pn], pn)
        all_tables.extend(tables)

    table_cell_texts = set()
    for t in all_tables:
        for cell in t["headers"]:
            table_cell_texts.add(cell.strip())
        for row in t["rows"]:
            for cell in row:
                table_cell_texts.add(cell.strip())

    blocks = []
    block_counter = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_height = page.rect.height
        page_blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for b in page_blocks:
            if b["type"] == 0:
                text = ""
                max_font_size = 0
                is_bold = False
                for line in b["lines"]:
                    for span in line["spans"]:
                        text += span["text"]
                        sz = round(span["size"], 1)
                        if sz > max_font_size:
                            max_font_size = sz
                        if "Bold" in span["font"] or "bold" in span["font"].lower():
                            is_bold = True
                    text += "\n"
                text = text.strip()
                if text and not is_page_footer(text, list(b["bbox"]), page_height):
                    block_counter += 1
                    blocks.append({
                        "id": block_counter,
                        "page": page_num + 1,
                        "text": text,
                        "font_size": max_font_size,
                        "is_bold": is_bold,
                        "bbox": list(b["bbox"]),
                    })

    filtered_blocks = []
    for b in blocks:
        lines = b["text"].split("\n")
        non_table_lines = [
            l for l in lines if l.strip() not in table_cell_texts
        ]
        if non_table_lines:
            cleaned = "\n".join(non_table_lines).strip()
            if cleaned:
                filtered_blocks.append({**b, "text": cleaned})

    elements = []
    skip = set()
    for i, b in enumerate(filtered_blocks):
        if i in skip:
            continue
        text = b["text"]
        is_bold = b["is_bold"]
        font_size = b["font_size"]

        is_heading = False
        section_num, heading_level = extract_heading_info(text)
        if section_num and ":" not in text:
            is_heading = True
        elif font_size >= 14:
            is_heading = True
            heading_level = 1
        elif font_size >= 12 and is_bold:
            is_heading = True
            heading_level = 1
        elif is_bold and len(text) < 120:
            is_heading = True
            heading_level = 1

        if is_heading:
            elements.append(ParsedElement(
                element_type="heading", text=text, page=b["page"],
                font_size=font_size, is_bold=is_bold, bbox=b["bbox"],
                heading_level=heading_level, section_number=section_num,
            ))
        else:
            paragraph_text = text
            skip.add(i)
            j = i + 1
            while j < len(filtered_blocks):
                nb = filtered_blocks[j]
                nb_text = nb["text"]
                nb_bold = nb["is_bold"]
                nb_fs = nb["font_size"]

                nb_is_heading = False
                nb_sn, nb_hl = extract_heading_info(nb_text)
                if nb_sn and ":" not in nb_text:
                    nb_is_heading = True
                elif nb_fs >= 12 and nb_bold:
                    nb_is_heading = True
                elif nb_bold and len(nb_text) < 120:
                    nb_is_heading = True

                if not nb_is_heading:
                    if NUMBERED_ITEM.match(nb_text.strip()) or NUMBERED_ITEM.match(paragraph_text.strip()):
                        break
                    vertical_gap = nb["bbox"][1] - b["bbox"][3]
                    same_page = nb["page"] == b["page"]
                    if same_page and 0 < vertical_gap < 20:
                        paragraph_text += " " + nb_text
                        skip.add(j)
                        b = nb
                        j += 1
                        continue
                break

            elements.append(ParsedElement(
                element_type="paragraph", text=paragraph_text, page=b["page"],
                font_size=font_size, is_bold=is_bold, bbox=b["bbox"],
            ))

    doc.close()

    tree = _build_tree_from_elements(elements, all_tables)
    return tree, all_tables


def _build_tree_from_elements(elements: List[ParsedElement],
                               tables: List[Dict]) -> List[TreeNode]:
    root_children: List[TreeNode] = []
    stack: List[TreeNode] = []
    numbered_buffer: List[str] = []

    def flush_list():
        nonlocal numbered_buffer
        if numbered_buffer and stack:
            parent = stack[-1]
            list_text = "\n".join(numbered_buffer)
            node = TreeNode(
                node_type="numbered_list",
                title="Numbered List",
                body_text=list_text,
                heading_level=0,
            )
            parent.children.append(node)
            numbered_buffer = []

    def add_tables_for_page(page_num: int, current_stack: List[TreeNode]):
        for t in tables:
            if t["page"] == page_num:
                parent = current_stack[-1] if current_stack else None
                if parent is None:
                    parent = TreeNode(node_type="section", title="root")
                    root_children.append(parent)
                table_text = "Headers: " + " | ".join(t["headers"]) + "\n"
                for row in t["rows"]:
                    table_text += " | ".join(row) + "\n"
                node = TreeNode(
                    node_type="table",
                    title="Table",
                    body_text=table_text.strip(),
                    heading_level=0,
                    page_number=page_num,
                )
                parent.children.append(node)

    pending_tables = list(tables)

    for elem in elements:
        if elem.element_type == "heading":
            flush_list()
            level = elem.heading_level if elem.heading_level > 0 else 1

            for t in pending_tables:
                if t["page"] == elem.page:
                    parent = stack[-1] if stack else None
                    if parent is None:
                        parent = TreeNode(node_type="section", title="root")
                        root_children.append(parent)
                    table_text = "Headers: " + " | ".join(t["headers"]) + "\n"
                    for row in t["rows"]:
                        table_text += " | ".join(row) + "\n"
                    table_node = TreeNode(
                        node_type="table",
                        title="Table",
                        body_text=table_text.strip(),
                        heading_level=0,
                        page_number=elem.page,
                    )
                    parent.children.append(table_node)
            pending_tables = [t for t in pending_tables if t["page"] != elem.page]

            while stack and stack[-1].heading_level >= level:
                stack.pop()

            node = TreeNode(
                node_type="heading",
                title=elem.text,
                section_number=elem.section_number,
                heading_level=level,
                page_number=elem.page,
            )

            if stack:
                stack[-1].children.append(node)
            else:
                root_children.append(node)
            stack.append(node)

        elif elem.element_type == "paragraph":
            if NUMBERED_ITEM.match(elem.text.strip()):
                numbered_buffer.append(elem.text.strip())
            else:
                flush_list()
                parent = stack[-1] if stack else None
                if parent is None:
                    parent = TreeNode(node_type="section", title="root")
                    root_children.append(parent)
                node = TreeNode(
                    node_type="paragraph",
                    body_text=elem.text,
                    page_number=elem.page,
                )
                parent.children.append(node)

    flush_list()

    for t in pending_tables:
        parent = stack[-1] if stack else None
        if parent is None:
            parent = TreeNode(node_type="section", title="root")
            root_children.append(parent)
        table_text = "Headers: " + " | ".join(t["headers"]) + "\n"
        for row in t["rows"]:
            table_text += " | ".join(row) + "\n"
        table_node = TreeNode(
            node_type="table",
            title="Table",
            body_text=table_text.strip(),
            heading_level=0,
            page_number=t["page"],
        )
        parent.children.append(table_node)

    return root_children
