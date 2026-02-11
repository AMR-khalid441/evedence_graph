got you. here’s a **clean, final, README-ready summary** you can drop in as-is.
no fluff, no back-and-forth — just the decisions and the reasoning.

---

## 📄 Chunking & Overlap Strategy (Final Design)

This project uses a **section-aware chunking strategy** tailored to scientific papers to maximize retrieval quality in a RAG pipeline.

---

### 1️⃣ Data Source & Preprocessing

* Papers are **scraped from the website**, not parsed from original PDFs.
* Clean, structured text is used to **generate controlled PDFs**.
* Chunks are separated using an explicit delimiter:

```
---
```

This ensures deterministic, layout-independent chunking.

---

### 2️⃣ Section-Aware Chunking Rules

Different sections are chunked using **different logic**, based on their semantic nature.

#### ✅ Results

* Chunked as **one atomic chunk**
* **No overlap**
* Self-contained, factual content

#### ✅ Conclusion

* Chunked as **one atomic chunk**
* **No overlap**
* Standalone summary content

#### 🔄 Discussion

* Chunked using **semantic chunking**
* Split into multiple chunks if large
* **Small overlap applied only between Discussion chunks**
* Overlap size: **~50–100 tokens**
* Overlap never crosses section boundaries

This preserves narrative continuity without semantic leakage.

---

### 3️⃣ Overlap Rules (Strict)

* ✔ Overlap: **Discussion → Discussion**
* ✘ No overlap:

  * Results → Discussion
  * Discussion → Conclusion
  * Any other cross-section combination

Overlap is applied **only during chunk generation**, not during retrieval.

---

### 4️⃣ Chunk Header Format (Mandatory)

Every chunk — including Discussion parts — includes the paper title in the text body:

```
Title: <Paper Title>
Section: <Section Name> (Part N)
```

This improves embedding quality and prevents cross-paper ambiguity.

---

### 5️⃣ Token Strategy

* Target chunk size: **300–600 tokens**
* Hard upper bound: **~800 tokens**
* If a Discussion chunk exceeds the limit:

  * It is further split semantically
  * Overlap is preserved only within Discussion

Results and Conclusion are never auto-split.

---

### 6️⃣ Metadata (for Vector DB)

Each chunk includes structured metadata:

```json
{
  "title": "...",
  "section": "discussion | results | conclusion",
  "part": 1,
  "chunk_strategy": "semantic_overlap | atomic",
  "has_overlap": true
}
```

Metadata complements — but does not replace — title inclusion in chunk text.

---

### 7️⃣ Design Philosophy

* Chunk **by meaning first**, tokens second
* Use **explicit structure over heuristics**
* Treat different sections according to how users query them
* Optimize for **retrieval quality, not uniformity**

---

### ✅ Final Verdict

This approach provides:

* High semantic integrity
* Controlled overlap where reasoning flows
* Clean, debuggable ingestion
* Production-ready RAG behavior

---

If you want, I can:

* polish this further for public GitHub
* add a small diagram
* or write a “Why not generic chunking?” section

But as it is — this is solid and professional 👌
