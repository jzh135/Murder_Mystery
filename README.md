# Murder Mystery (剧本杀) Webapp

An AI-powered local multiplayer murder mystery game.

## Tech Stack

- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Backend**: FastAPI + LangGraph + SQLite
- **AI**: Google Gemini 2.0 Flash

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- Google AI API Key

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev -- --host
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

For LAN play, use your machine's IP address instead of localhost.

## Adding Custom Stories

Place story JSON files in `backend/stories/`. See `backend/stories/schema.md` for the format.

## License

MIT
