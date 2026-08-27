# Module 4 — Driving Academy Assistant

Owner: **You**  
Status: **Active — Ready to Build**

## Overview
The chat widget and assistant where a learner describes driving challenges during their 30-day practice window and receives the best matching instructional video.

## Key Design Principles (from AGENTS.md Section 5.4)
- **10 Curated Topics**: Pre-generated instructional clips (8-turn, reverse parking, hill start, clutch control, steering, lane change, parallel parking, emergency braking, mirror & signal checks, gradient descent).
- **Classification vs Embeddings**: Uses single LLM classification rather than complex embeddings pipelines at this scale.
- **No live video generation**: Delivers existing video clips with high confidence.

## Running Independently
From repository root:
```powershell
uv run --package academy-service uvicorn academy_service.main:app --reload --port 8004
```
- Interactive Swagger UI: `http://localhost:8004/docs`

## Testing
```powershell
uv run pytest services/academy
```
