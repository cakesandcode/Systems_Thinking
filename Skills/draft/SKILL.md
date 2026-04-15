# draft

**Role:** Produce publication-ready drafts for Substack and LinkedIn using only verified claims from the Obsidian vault research corpus. Flag any claim that lacks a source rather than speculate.

---

## When to invoke
- A new analysis is complete in `Systems_Thinker/raw/` and ready for publication
- Human requests a draft of a specific format
- A prior draft needs a revision pass

---

## Inputs
- **analysis** — Folder name under `Systems_Thinker/raw/` (e.g., `Chip_to_rack`) (required)
- **format** — substack-post | linkedin-text | linkedin-carousel (required)
- **audience** — architect | engineer | executive (default = architect)
- **word_target** — approximate word count (optional, soft limit)

---

## Format Selection Guide

Before drafting, ask: **"Is the content a visual story with 3+ distinct panels, or a single argument with supporting data?"**

| Answer | LinkedIn format | Why |
|---|---|---|
| Visual story (charts, tables, step-by-step flow) | **linkedin-carousel** | PDF carousels get highest engagement for technical content. Each slide = one idea. |
| Single argument + 1 key visual | **linkedin-text** | Text post + attached screenshot. Simpler, faster to publish. |

**Always produce the substack-post first.** The LinkedIn draft is derived from it — same facts, compressed format.

---

## Process

### Step 1 — Read source corpus
Read all `.md` files in `Systems_Thinker/raw/{analysis}/`.
Also read any related files in supporting folders (`Cold_plates/`, `GPU_specifications/`, etc.).

These are the ONLY citable sources. Do not invent figures, specs, or claims.

### Step 2 — Check readiness
If the analysis folder has no substantive `.md` file with equations, tables, or conclusions:
- Report: "BLOCKED — analysis not complete. Missing: [description]"
- Do not proceed.

### Step 3 — Plan structure
Output a brief section outline (3–8 items) to confirm structure before drafting.

### Step 4 — Write draft

#### substack-post
- YAML frontmatter: `title`, `subtitle`, `slug`, `tags`, `canonical_url`, `description`, `author`, `date`
- Open with a concrete hook — a problem, an insight, or a framework reference
- One idea per section. Sections use H2 headers.
- Every factual claim traceable to the source `.md` files
- Inline hyperlinks on key references (link to source URLs from the research .md files)
- Code blocks for equations
- Image placement markers (Substack does not render markdown images — use explicit markers):
  `[INSERT IMAGE: screenshots/filename.png]` followed by `*Caption: description*`
  These tell the author exactly where to drag-and-drop images when pasting into Substack's editor
- **All tables must also be rendered as PDF files** in `screenshots/` using the dark theme (black bg, cyan headers, color-coded levels). The PDF is the publishable asset; the markdown table is the source of truth. Generate PDFs using fpdf2 with Arial Unicode font for glyph support.
- No marketing language. No hedging without basis.
- Numbered sources section at the bottom with full URLs
- Punchy title that poses a question or makes a claim

**Output:** `Systems_Thinker/raw/{analysis}/{slug}-substack-post.md` — paste body into Substack editor, fill metadata from frontmatter, attach screenshots.

#### linkedin-text
- YAML frontmatter: `title`, `tags`, `linked_substack`, `linked_repo`, `image`
- Max 1300 characters body (soft limit)
- Hook in first 2 lines (visible before "see more")
- No bullet lists — short punchy paragraphs
- Bold for structure: **Chip wins:**, **Rack wins:**, etc.
- One clear CTA at end (repo link + Substack link)
- Hashtags at end, no hashtags in body. **Must include every brand/product name mentioned in the post** (HP SiCP, NVIDIA, JetCool, etc.) plus 3-4 topic tags
- Title as H1 — statement or question, not a label
- No inline sources — the Substack carries citations

**Output:** `Systems_Thinker/raw/{analysis}/{slug}-linkedin.md` — copy body text (without frontmatter) into LinkedIn composer, attach the image from `image` field.

#### linkedin-carousel
- YAML frontmatter: `title`, `tags`, `linked_substack`, `linked_repo`, `slides`
- Design as 5–8 slides, each slide = one idea
- Slide structure:
  - **Slide 1:** Hook title + subtitle (same as the LinkedIn text hook)
  - **Slides 2–N:** One key point per slide. Large text, minimal detail. A chart or table if visual.
  - **Final slide:** CTA — repo link, Substack link, author handle
- Each slide described as a markdown section with `### Slide N — title`
- Include companion text post (short, ~500 chars) that teases the carousel content
- Screenshots from the app become carousel slides where appropriate

**Output:**
- `Systems_Thinker/raw/{analysis}/{slug}-linkedin-carousel.md` — slide descriptions + companion text
- The actual PDF is produced separately (e.g., in Canva or from the slide descriptions)

---

### Step 5 — Flag unverified gaps
Any sentence relying on a claim not in the source `.md` files:
- Replace with: [NEEDS SOURCE: {description}]
- Add to "Claims requiring verification" checklist at end of draft

### Step 6 — Write draft files
Write to `Systems_Thinker/raw/{analysis}/` using the naming convention above.

### Step 7 — Report
Output:
- Draft file path(s)
- Word count / character count
- Number of source citations used
- Number of [NEEDS SOURCE] flags
- Recommended next action

---

## Output files per analysis

```
Systems_Thinker/raw/{analysis}/
├── {slug}-substack-post.md        # Paste into Substack (markdown + metadata)
├── {slug}-linkedin.md             # Copy body into LinkedIn (text + image)
├── {slug}-linkedin-carousel.md    # Optional: slide descriptions for PDF carousel
└── screenshots/                   # Images and table PDFs for both platforms
    ├── app_top.png                # App screenshots
    ├── app_bottom.png
    └── {table_name}.pdf           # Rendered tables (dark theme, color-coded)
```

---

## Rules
- Never invent a performance figure, spec, or product name not in the source files.
- [NEEDS SOURCE] is correct output for missing facts — not a failure.
- Tone is Aruna Kumar's voice: direct, precise, no filler. Write for practitioners who build systems, not for marketers.
- Do not pad to hit a word target. Shorter and accurate beats longer and hedged.
- Always produce substack-post first, then derive LinkedIn from it.
- GitHub repo: github.com/cakesandcode/Systems_Thinking
- Substack: armfirmware.substack.com
