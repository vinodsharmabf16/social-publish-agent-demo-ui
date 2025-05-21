# social-publish-agent-demo-ui

## Directory Structure
- `drafts/` (create if not present)
- `response/` (create if not present)

## How to Start the Servers

### Gradio (UI)
```bash
watchmedo auto-restart --patterns="*.py" --recursive -- python3 app.py
```

### Backend
```bash
cd backend
uvicorn api:app --reload
```

### Trending API
```bash
cd trending_topics
uvicorn api_configuration:app --host 0.0.0.0 --port 8008 --reload
```