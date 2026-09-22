---
name: academic-doc-formatting
description: "реферат, титульник, контрольная работа, оглавление, задание, практическая работа. Formats academic DOCX documents with verified title page layout, branch-specific structure (full papers vs routine tasks), and strict pagination."
---

# Academic Document Formatting (DOCX)

Use when generating student term papers, essays, control works (`контрольная работа`), reports (`реферат`), or practical assignments (`задание`, `практическая работа`, `этап проекта`) as `.docx` files requiring an official university title page (`титульный лист`) and verified layout.

## 1. Document Category Selection

Before building the document structure, select the exact category requested by the user:

- **Category A: Full Academic Papers (`реферат`, `курсовая работа`):**
  - Section 1: Title page (strictly 1 page).
  - Section 2: Table of Contents (`СОДЕРЖАНИЕ`, strictly page 2).
  - Section 3+: `ВВЕДЕНИЕ`, chapters on separate pages, `ЗАКЛЮЧЕНИЕ`, and `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ` (GOST 7.0.100-2018).
- **Category B: Routine Assignments & Tasks (`задание`, `практическая работа`, `решение задач`, `этап проекта`):**
  - **Simplified structure:** Do **NOT** generate a Table of Contents (`СОДЕРЖАНИЕ`) or References list (`СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ`).
  - Section 1: Title page (strictly 1 page).
  - Section 2+: Starts directly on page 2 with the task title, conditions, problem solutions, analytical tables, and diagrams.

## 2. Title Page (`титульный лист`) Layout & Spill Prevention

A title page must occupy **strictly one page** and never spill onto page 2, while maintaining correct vertical distribution:
- **Header:** Ministry & University name centered at top (`y0 ≈ 57–120 pt`, font size 11–12 pt, 1.15 line spacing).
- **Center Block:** Discipline, work kind, and Topic centered (`y0 ≈ 230–320 pt`).
- **Author/Supervisor Block:** Right-aligned, placed strictly in the **lower third** of the page (`y0 ≈ 600–620 pt`).
  - *Pitfall:* Do not shrink spacer paragraphs between topic and author block too aggressively (e.g., down to 20 pt), or the author block will float unnaturally into the middle of the sheet. Keep spacers calibrated (~65–72 pt across 3 spacer paragraphs).
- **City & Year:** Centered, anchored strictly at the bottom margin (`y0 ≈ 755–770 pt` on 842 pt A4 height, e.g. `Астрахань, 2026.`).
  - Keep the spacer before the city/year paragraph at ~20–25 pt so it does not push onto page 2.
- **Section Break:** Always terminate the title page with a hard section break (`doc.add_section(WD_SECTION_START.NEW_PAGE)`), not a soft page break.
- **Indent rule on Title Page:** Set `paragraph_format.first_line_indent = Inches(0)` on all title page paragraphs without exception. Any inherited first-line indent skews centered and right-aligned text.

## 3. First-Line Indent (Красная строка) Rules

Follow standard academic GOST rules for paragraph indentation:
- **Body paragraphs:** Strict first-line indent of **1.25 cm** (`Inches(0.49)` / `448310 dxa`) and justified alignment (`WD_ALIGN_PARAGRAPH.JUSTIFY`).
- **Zero-indent elements (strictly `Inches(0)`):**
  - All title page paragraphs (header, title, author/supervisor, city/year).
  - All section and subsection headings.
  - All table cells (interior paragraph indents break cell alignment).
  - Table captions (`Таблица 1`) and figure captions (`Рис. 1. ...`).
  - Centered images and formulas.

## 4. Schemas, Diagrams & High-DPI Graphic Insets

When an academic assignment requires a flowchart, supply chain map, or process schema with Russian text:
- **Do NOT use AI image diffusion models (e.g. Grok Imagine, DALL-E) for schemas containing body text:** Diffusion models blur, artifact, and distort small Cyrillic lettering inside table cells and labels.
- **Generate vector / HTML-rendered graphics:** Use clean HTML/CSS with standard Cyrillic sans fonts (Liberation Sans, DejaVu Sans), flexbox/grid layout, and render to high-DPI PNG via `wkhtmltoimage` (`--zoom 1.5 --width 1560`) or SVG via `inkscape`. This guarantees 100% crisp, readable text and professional visual quality when embedded in `.docx`.

## 5. Table of Contents (`СОДЕРЖАНИЕ`) Layout (Category A Only)

- Place `СОДЕРЖАНИЕ` in Section 2, immediately following the title page section break.
- **Typography:** All TOC text and page numbers must use `Times New Roman` (12–13 pt) matching body text.
- **Tab Stops & Dot Leader:** Format each line with right-aligned tab stops and dot leader (`WD_TAB_LEADER.DOTS`) at the right margin (6.5 inches / 16.5 cm for A4 with 3 cm left / 1.5 cm right margins).
  ```python
  p.paragraph_format.tab_stops.add_tab_stop(Inches(6.5), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
  p.add_run(title)
  p.add_run("\t")
  p.add_run(page_str)
  ```
- **Page Isolation:** Terminate the TOC with another `WD_SECTION_START.NEW_PAGE` section break so that `ВВЕДЕНИЕ` begins strictly on Page 3.

## 6. Structural Section Isolation

- In Category A works, major structural blocks (`ВВЕДЕНИЕ`, `1. ...`, `2. ...`, `3. ...`, `ЗАКЛЮЧЕНИЕ`, `СПИСОК ИСПОЛЬЗОВАННЫХ ИСТОЧНИКОВ`) must each begin on a fresh page (`WD_SECTION_START.NEW_PAGE` or `p.add_run().add_break(WD_BREAK.PAGE)`).
- In Category B tasks, keep subsections flowing logically with standard paragraph spacing (`space_before=10 pt`, `space_after=4 pt`), breaking pages only where diagrams or large tables require clean isolation.

## 7. Post-Render Verification (Headless LibreOffice + PyMuPDF)

Always convert the `.docx` to `.pdf` and verify layout via script before delivering:
```bash
libreoffice --headless --convert-to pdf --outdir /tmp /tmp/doc.docx
```

Inspect page bounds with PyMuPDF:
```python
import fitz
doc = fitz.open("/tmp/doc.pdf")

# 1. Verify title page strictly occupies Page 1
page1_text = doc[0].get_text()
assert "Министерство" in page1_text and "Астрахань" in page1_text, "Title page spilled onto page 2!"

# 2. Category A: Verify exact TOC page numbers via two-pass inspection
# 3. Category B: Verify page 2 begins with task body (no orphaned TOC or empty pages)
page2_text = doc[1].get_text()
assert "СОДЕРЖАНИЕ" not in page2_text, "TOC incorrectly generated in Category B task!" # for tasks
```

## 8. Encoding & Typo Sanitization

When generating Russian text into `.docx` files via python scripts:
- Never embed multi-byte heredocs directly in bash without verifying clean UTF-8 string encoding.
- Always run an automated sweep removing replacement characters (`\ufffd`) or unprintable control codes:
  ```python
  for p in doc.paragraphs:
      for r in p.runs:
          r.text = "".join(c for c in r.text if ord(c) != 0xfffd and ord(c) < 0x10000 and ord(c) != 0)
  ```
- Automatically scan the generated text against known truncation artifacts (e.g. `рактиче` instead of `практиче`, doubled letter prefixes, truncated headings).
- Verify `bad_chars == 0` before sending the attachment to the user.
