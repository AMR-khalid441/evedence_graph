# EvidenceGraph

## Overview
**EvidenceGraph** is a domain-specific research intelligence system that transforms fragmented mental health research into connected, citation-backed evidence.

Instead of reading hundreds of long PDFs, users can ask clear questions like:

> *"What mental health factors predict postpartum depression?"*

and receive answers synthesized **across many studies**, grounded in **Results and Conclusions**, with **verifiable citations**.

EvidenceGraph is not a general chatbot. It is an **evidence system**.

---

## Problem
Mental health research suffers from:

- Thousands of papers spread across multiple authoritative websites
- Long, dense PDFs that are time-consuming to read
- Inconsistent terminology across studies
- No fast way to aggregate findings across the literature

Today, answering a single research question often requires:
1. Searching multiple databases
2. Opening dozens of papers
3. Manually reading Results and Conclusions
4. Comparing findings by hand
5. Tracking citations manually

This process is slow, error-prone, and cognitively expensive.

---

## Solution
EvidenceGraph compresses this entire workflow.

It:
- Extracts **Results and Conclusions** from peer-reviewed mental health studies
- Normalizes equivalent concepts across papers
- Aggregates evidence across multiple sources
- Answers questions using **only verified research findings**
- Attaches **citations (PMCID / PMID / DOI)** to every claim

The result is fast, trustworthy access to what the scientific literature actually says.

---

## Key Principles

### 1. Evidence over language
EvidenceGraph does not generate opinions.
It surfaces **what studies report**, not what a model believes.

### 2. Aggregation over summarization
Single-paper summaries are low value.
EvidenceGraph focuses on **patterns across many studies**.

### 3. Traceability by default
Every answer is backed by clickable, verifiable citations.

### 4. Domain focus
The system is optimized for **mental health research**, enabling higher accuracy and better normalization.

---

## What EvidenceGraph Is NOT

- ❌ A medical diagnosis tool
- ❌ A replacement for clinicians
- ❌ A general-purpose chatbot
- ❌ A full-paper reader

EvidenceGraph is a **decision-support and research assistance tool**.

---

## Data Scope

### Included
- Results sections
- Conclusions sections
- Study metadata (title, authors, journal, year, identifiers)

### Excluded
- Methods details
- Raw PDFs for end users
- Clinical recommendations without evidence

This high-signal approach improves retrieval quality and reduces noise.

---

## Sources
EvidenceGraph ingests data from authoritative, publicly available sources, starting with:

- PubMed Central (PMC)

The system is designed to scale to additional trusted sources such as:
- Public health organizations
- Clinical guidelines
- Government research repositories

---

## Example Question

**User asks:**
> *What mental health factors predict postpartum depression?*

**EvidenceGraph responds with:**
- Antepartum mental health: strongest predictor (reported consistently across studies)
- Pre-pregnancy mental health history: significant independent predictor
- Socioeconomic disparities: frequently associated factor
- Prevalence range across studies

Each point includes citations linking directly to the original research articles.

---

## How It Works (High Level)

1. Scrape Results and Conclusions from trusted sources
2. Extract and normalize mental health concepts
3. Store structured evidence with metadata
4. Aggregate findings across studies
5. Answer questions using evidence-backed retrieval

---

## Why Not Just Use ChatGPT?

ChatGPT generates answers.

EvidenceGraph provides **evidence-backed answers**.

Key differences:
- Fixed, auditable corpus
- Deterministic and reproducible outputs
- Explicit aggregation across studies
- Guaranteed citations for every claim

EvidenceGraph complements large language models rather than replacing them.

---

## Intended Users

- Students conducting literature reviews
- Early-stage researchers
- Public health analysts
- Mental health NGOs
- Digital health startups
- Medical writers and educators

---

## Ethics & Responsibility

EvidenceGraph:
- Does not provide medical advice
- Does not replace professional judgment
- Encourages users to consult original sources

The system is designed to support responsible use of scientific evidence.

---

## Roadmap

- Improve concept normalization
- Add evidence strength scoring
- Expand trusted data sources
- Support additional research domains

---

## Project Status
This project is under active development.

The current focus is building a **robust, trustworthy evidence foundation** before expanding features or domains.

---

## License
This project uses publicly available research content in accordance with source licenses.

---

## Final Note
EvidenceGraph exists to answer one question well:

> *"What does the scientific evidence actually say?"*

Everything else is secondary.

