"""FastAPI entrypoint for Module 4 (Driving Academy Assistant)."""

from contracts.academy import AcademyVideo, VideoMatchRequest, VideoMatchResult
from fastapi import FastAPI, HTTPException

from academy_service.catalog import get_all_videos, get_video_by_id
from academy_service.matcher import VideoMatcher

app = FastAPI(
    title="Parivahan Driving Academy Assistant",
    version="0.1.0",
    description="Module 4: AI-assisted Driving Academy matching learner queries to ~10 curated skill clips.",
)

matcher = VideoMatcher()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "academy-service"}


@app.get("/academy/videos", response_model=list[AcademyVideo])
def list_videos() -> list[AcademyVideo]:
    """Retrieve the full library of Driving Academy video clips."""
    return get_all_videos()


@app.get("/academy/videos/{video_id}", response_model=AcademyVideo)
def get_video(video_id: str) -> AcademyVideo:
    """Retrieve a single video by ID."""
    video = get_video_by_id(video_id)
    if not video:
        raise HTTPException(status_code=404, detail=f"Video '{video_id}' not found")
    return video


@app.post("/academy/match-video", response_model=VideoMatchResult)
def match_video(request: VideoMatchRequest) -> VideoMatchResult:
    """Match a learner's query or difficulty to the best instructional video."""
    return matcher.match(request)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("academy_service.main:app", host="127.0.0.1", port=8004, reload=True)
