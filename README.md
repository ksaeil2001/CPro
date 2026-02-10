# Manga Translator

만화/웹툰 이미지 기반 자동 번역 서비스 (일본어 → 한국어)

## Features

- 텍스트 영역 자동 감지 (CRAFT)
- OCR (PaddleOCR + Google Vision 폴백)
- LLM 번역 (GPT-4o-mini)
- 인페인팅으로 원본 텍스트 제거 (LaMa)
- 한국어 식자 자동 삽입 (Pillow)
- 단계별 비용 추적 및 로깅

## Tech Stack

- **Frontend**: Next.js 15, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **Database**: PostgreSQL 16
- **ML**: CRAFT, PaddleOCR, LaMa, GPT-4o-mini

## Quick Start

```bash
# Copy environment variables
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker compose up --build

# Run database migrations
make migrate
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

## Project Structure

```
├── backend/          # FastAPI + translation pipeline
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── core/     # config, database
│   │   ├── models/   # SQLAlchemy models
│   │   ├── pipeline/ # 11-stage translation pipeline
│   │   ├── schemas/  # Pydantic models
│   │   └── services/ # cost tracking, circuit breaker
│   └── tests/
├── frontend/         # Next.js UI
│   └── src/
│       ├── app/      # pages
│       ├── components/
│       ├── hooks/
│       └── lib/      # API client, types
└── shared/           # shared constants
```
