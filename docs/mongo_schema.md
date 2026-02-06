{
    "_id": ObjectId(),               // Mongo unique ID
    "source": "PMC",
    "source_url": "https://pmc.ncbi.nlm.nih.gov/...",
    "section": "Results",            // or "Conclusions" //discussion one // discussion 2
    "raw_text": "Antepartum depression was consistently associated...",
    "study_metadata": {
        "title": "...",
        "journal": "...",
        "year": 2021,
        "pmid": "...",
        "pmcid": "...",
        "doi": "..."
    },
    "status": "raw",                  // raw | processed | rejected
    "ingested_at": ISODate(),
    "hash": "sha256(raw_text + pmcid)"
}
