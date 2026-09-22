---
name: a4-text-sheet
description: "на листе, оформи сочинение, раскраска, расписание, техника чтения. Renders school homework and reading sheets as decorated A4 2480×3508 and a chat JPEG; print only if asked."
---

# A4 Text Sheet

When the user wants school or homework text on a sheet, decorated, colored-in, a timetable, a reading technique sheet (`техника чтения`), a number table, or ready to print.

## Before drawing

1. Do not render until the source is in the chat (paste or photo). Ask once for missing text, title, and whether to print a name.
2. Illustration theme = the title or topic the user stated. Do not invent a hometown scene (river, lotuses, Kremlin) unless they named that place.

## Pictures

3. If they want a picture or a coloring page (`разукрасить`, `раскраска`), generate the art first, inspect it with `view_image`, then compose it into the HTML as a `file://` image.
   - Coloring page: black outlines, white background, no gray, shading, or fills; large regions.
   - Grok: `~/scripts/grok_image.sh "PROMPT" OUT.png grok-imagine-image 3:4` with a 300s exec timeout. Do not use `image_generate` for Grok — that path stalls at 30s. If they asked for Grok, do not substitute a local SVG drawing.

## Make the page

4. Write a self-contained HTML page whose root is exactly **2480×3508** (A4 @ 300 dpi, portrait). Load Cyrillic with `@font-face` from `file:///usr/share/fonts/truetype/noto/NotoSerif-Regular.ttf` (Bold/Italic and `NotoSerifDisplay` as needed). Use the write tool, not a shell heredoc.
5. Render with:

```
wkhtmltoimage --encoding utf-8 --width 2480 --height 3508 --quality 100 --enable-local-file-access PAGE.html PAGE.png
```

Do not use `snap run chromium` — the chromium snap is not installed. Do not use `firefox --headless --screenshot` — it stays running and never writes the file.

6. wkhtmltoimage layout (Qt WebKit) & Typography:
   - **Font sizing for children's reading sheets:** Body text read aloud by elementary students (e.g. 4th grade техника чтения) must be at least **38–40px** @ 300 dpi (line-height 1.5). 34px is too small for comfortable reading.
   - **Reading technique layout (`техника чтения`):** Keep story text completely clean of bracketed numbers. Place cumulative word counts in a dedicated right-margin column (`.count-col`, ~30px bold gray) so the timer can check words without distracting the child. Include 2 comprehension questions per text and a compact tracking table («Дневник чтения»: Дата, Текст, Слов за 1 мин, Ошибок, Понимание) at the bottom.
   - `gap` is ignored — number and word glue together. Use `padding-right` on the number cell.
   - `display:table` on rows inside a column stacks every row at the top. Use explicit row heights or `-webkit-box`, not table display, to fill the column.
   - Do not put Russian headings in `h2` with NotoSerifDisplay — letters break (н→и). Use a `div` with NotoSerif Bold.
7. Confirm the PNG is 2480×3508, then inspect it with `view_image` before sending. Fix overflow, glued text, missing fonts, cut-off text, or header/art overlap and re-render until the sheet is readable. Keep that PNG; do not overwrite it with a later variant.

## Deliver

8. Send a JPEG (~quality 92) to chat. A full-A4 PNG is tens of megabytes and is the print master, not the chat file. Even when they already asked to print, send this preview from a passing `view_image` first, then print.
9. Print only after an explicit ask. Print the PNG of the preview they replied to, not a later overwrite. Portrait 2480×3508 only — `print_xerox.sh` stretches any other size.

```bash
~/scripts/print_xerox.sh /path/to/PAGE.png
```

Do not use `nc ... 9100` (port 9100 drops PXL silently) or raw `lpr` via snap cups (CUPS snap queue breaks periodically). The script converts to AirPrint `image/urf` and dispatches via IPP directly to the printer.

If the script exits 1, do not rerun it. Write RGB PNG, PDF, and URF under `~/print/` (snap cups cannot use `/tmp`), then:

```
snap run cups.cupsfilter -P ~/print/xerox.ppd -i application/pdf -m image/urf -o media=iso_a4_210x297mm -o print-color-mode=monochrome ~/print/PAGE.pdf > ~/print/PAGE.urf
snap run cups.ipptool -tv -f ~/print/PAGE.urf -d filetype=image/urf -d filename=~/print/PAGE.urf ipp://<printer-ip>/ipp/print print-job.test
```

Verify job completion with:
```bash
snap run cups.ipptool -tv ipp://<printer-ip>/ipp/print get-completed-jobs.test
```
Done when job-state-reasons is `job-completed-s`. `document-format` means the URF is invalid — regenerate with cupsfilter; do not resend PXL.
