---
title: Resume Matcher
sdk: docker
app_port: 7860
---

# Resume Matcher

FastAPI resume/JD matching app.

## Local run

```bash
pip install -r app/requirements.txt
USE_FALLBACK_TFIDF=true uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

## Render settings

- Build Command: `pip install -r app/requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment Variable: `USE_FALLBACK_TFIDF=true`
