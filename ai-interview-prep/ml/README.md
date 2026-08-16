# ml/

**Owner: ML Pair 1 (Question Generation) + ML Pair 2 (Scoring)**

This directory is the home for all machine-learning scripts that will power
the AI features of the interview prep companion.

---

## Planned contents

```
ml/
├── data/                    # Raw and cleaned Q&A datasets
├── ingestion/
│   ├── ingest.py            # Script to parse datasets → vector store
│   └── clean.py             # Data cleaning / deduplication
├── embeddings/
│   └── embed.py             # Batch-embed questions/answers (OpenAI / sentence-transformers)
├── evaluation/
│   ├── eval_scoring.py      # Offline evaluation of the scoring pipeline
│   └── metrics.py           # Cohen's kappa vs human labels
└── notebooks/
    └── exploration.ipynb    # EDA and prototyping
```

---

## Getting started

1. Install extra ML deps (not in `backend/requirements.txt` to keep the API lightweight):
   ```bash
   pip install sentence-transformers faiss-cpu openai chromadb
   ```

2. Set up your API keys in `ml/.env` (never commit this file):
   ```
   OPENAI_API_KEY=...
   ```

3. Run ingestion to populate the vector store before starting the backend:
   ```bash
   python ml/ingestion/ingest.py
   ```

---

## Hooks into the backend

Once ready, ML code slots into these stubs in `backend/app/services/`:

| Service file | Pair |
|---|---|
| `question_generation.py` | ML Pair 1 |
| `vector_store.py`        | ML Pair 1 |
| `scoring.py`             | ML Pair 2 |

Do **not** modify the function signatures — only fill in the implementations.
