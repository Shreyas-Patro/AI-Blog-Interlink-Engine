# AI Link Engine

AI-powered internal linking engine that semantically analyzes markdown content, generates high-quality anchor text using LLMs, and injects contextual links with human-in-the-loop review.

---

## Overview

The AI Link Engine transforms isolated blog posts into a connected content graph.

Instead of relying on keyword matching, it:

* Understands **meaning** using embeddings
* Finds **semantically related sections** across articles
* Uses an **LLM to generate natural anchor text**
* Requires **human approval (HITL)** before modifying files
* Safely injects links into markdown with multiple safeguards

---

## Features

* Semantic chunking of markdown articles
* Embedding-based similarity matching (cosine similarity)
* LLM-powered anchor text generation
* Human-in-the-loop review dashboard (Streamlit)
* Safe markdown injection with backup + validation
* Full pipeline caching (article, embedding, anchor levels)
* Rerun system for failed stages

---

## Tech Stack

* Python 3.11
* SQLAlchemy + SQLite
* Sentence Transformers (all-MiniLM-L6-v2)
* NumPy
* Anthropic Claude (for anchor generation)
* Streamlit (dashboard)
* Typer (CLI)

---

## Project Structure

```
link_engine/
│
├── db/                # Database models and session
├── stages/            # Pipeline stages
│   ├── ingest.py
│   ├── chunk.py
│   ├── embed.py
│   ├── match.py
│   ├── anchor.py
│   ├── inject.py
│
├── dashboard/         # Streamlit HITL UI
├── reports/           # Output reports
├── cli.py             # CLI entrypoint
```

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/ai-link-engine.git
cd ai-link-engine
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\\Scripts\\activate      # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set environment variables

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_api_key_here
```

---

## How It Works

Pipeline stages:

1. **Ingestion** → Reads markdown files + detects changes
2. **Chunking** → Splits content into semantic sections
3. **Embedding** → Converts chunks into vectors
4. **Matching** → Finds similar chunks across articles
5. **Anchor Generation** → LLM generates anchor text
6. **Review (HITL)** → Human approves/rejects links
7. **Injection** → Links inserted into markdown
8. **Reporting** → Outputs logs + summaries

---

## Execution Guide

### Step 1 — Add your content

Place markdown files inside a folder:

```
posts/
  article1.md
  article2.md
```

Each file must have frontmatter:

```yaml
---
title: Example Article
slug: example-article
url: https://yourblog.com/example-article
---
```

---

### Step 2 — Run the pipeline

```bash
python -m link_engine.cli run ./posts
```

What happens:

* Articles are ingested
* Chunks created
* Embeddings computed
* Matches found
* Anchor suggestions generated

---

### Step 3 — Start review dashboard

```bash
streamlit run link_engine/dashboard/app.py
```

Open in browser:

```
http://localhost:8501
```

Review each suggestion:

* Approve
* Reject
* Edit anchor text

---

### Step 4 — Inject links

Inside dashboard:

* Go to **Inject Approved** tab
* Disable dry run
* Click **Inject Links**

System will:

* Create `.bak` backups
* Insert links safely
* Log all operations

---

### Step 5 — View reports

Check generated files:

```
reports/
  link_report.json
  error_report.json
  run_summary.md
```

---

## Rerun Failed Steps

Retry only failed parts of pipeline:

```bash
python -m link_engine.cli rerun --stage anchor
python -m link_engine.cli rerun --all-errors
```

---

## Safety Features

* File hash verification before injection
* Automatic backups (`.bak` files)
* No injection inside:

  * code blocks
  * existing links
  * first 150 characters
* Chunk-scoped search (no wrong placements)
* Back-to-front insertion to preserve offsets

---

## Example Output

Before:

```
This guide covers effective link building strategies for SEO.
```

After:

```
This guide covers [effective link building strategies](https://example.com/domain-authority) for SEO.
```


---

## Contributing

PRs welcome. For major changes, open an issue first.

---


---

## Author

Shreyas Patro

---

## Vision

This project aims to build a **semantic content graph engine** that automates one of the highest-ROI SEO tasks — internal linking — with precision, safety, and intelligence.
