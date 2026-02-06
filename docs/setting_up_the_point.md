{
    "id": "63f9a9b2e4b0c123456789ab",
    "vector": [0.012, 0.884, ...],  // embedding of the claim
    "payload": {
        "text": "Antepartum depression strongly predicts postpartum depression",
        "pmid": "12345678",
        "pmcid": "PMC987654",
        "doi": "10.1234/abcd",
        "year": 2021,
        "title": "Predictors of Postpartum Depression Study",
        "source": "PMC",
        "concepts": ["antepartum depression", "postpartum depression"]
    }
}
the point should be in that shape 
, how um going to scrape ?
, i need the data in mongo db to be very close to that shape 


this how payload should look like

{
    "id": "63f9a9b2e4b0c123456789ab",
    "vector": [0.012, 0.884, ...],
    "payload": {
        "text": "Antepartum depression strongly predicts postpartum depression",  // the claim itself
        "pmid": "12345678",       // PubMed ID
        "pmcid": "PMC987654",     // PubMed Central ID
        "doi": "10.1234/abcd",    // DOI
        "year": 2021,             // Publication year
        "title": "Predictors of Postpartum Depression Study",
        "source": "PMC",
        "concepts": ["antepartum depression", "postpartum depression"]
    }
}

Payload = any extra info you want Qdrant to store with the point

Always include:

The text/claim

IDs for traceability

Filters (year, source, concepts)

Never put the embedding in the payload (that’s separate)