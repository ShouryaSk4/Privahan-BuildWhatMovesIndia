"""Driving Academy video catalog (Module 4).

Target: ~10 pre-generated instructional clips covering practical driving test skills.
Topics 1-5 explicitly named in Section 5.4; Topics 6-10 from Section 10.6.
"""

from contracts.academy import AcademyVideo

ACADEMY_VIDEO_CATALOG: list[AcademyVideo] = [
    AcademyVideo(
        video_id="vid_01_eight_turn",
        topic="8-turn",
        title="Mastering the Figure-8 Driving Track",
        description="Clear step-by-step steering wheel hand-over-hand technique and reference points for the RTO 8-track test.",
        duration_seconds=185,
        video_url="https://assets.parivahan.internal/videos/academy/01_eight_turn.mp4",
        tags=[
            "8-turn",
            "8 turn",
            "8 track",
            "8-track",
            "figure 8",
            "figure-8",
            "eight turn",
            "rto track",
            "test track",
        ],
    ),
    AcademyVideo(
        video_id="vid_02_reverse_parking",
        topic="reverse parking",
        title="Flawless Reverse & Bay Parking",
        description="How to align mirrors, use 45-degree angle entry, and park in reverse without touching track cones.",
        duration_seconds=210,
        video_url="https://assets.parivahan.internal/videos/academy/02_reverse_parking.mp4",
        tags=["reverse parking", "reverse", "parking", "cones", "bay parking", "s-track"],
    ),
    AcademyVideo(
        video_id="vid_03_hill_start",
        topic="hill start",
        title="Hill Start & Incline Control without Rollback",
        description="Using handbrake-clutch coordination to start smoothly uphill on the RTO incline ramp without rollback.",
        duration_seconds=195,
        video_url="https://assets.parivahan.internal/videos/academy/03_hill_start.mp4",
        tags=["hill start", "incline", "slope", "ramp", "rollback", "handbrake", "uphill"],
    ),
    AcademyVideo(
        video_id="vid_04_clutch_control",
        topic="clutch control",
        title="Finding the Clutch Biting Point",
        description="Preventing engine stalling in slow traffic and smooth gear shifts using clutch friction point mastery.",
        duration_seconds=160,
        video_url="https://assets.parivahan.internal/videos/academy/04_clutch_control.mp4",
        tags=["clutch control", "clutch", "biting point", "stalling", "gear shift", "engine stall"],
    ),
    AcademyVideo(
        video_id="vid_05_steering",
        topic="steering",
        title="Steering Techniques: Push-Pull vs Hand-over-Hand",
        description="Correct steering wheel grip (9-and-3 position) and smooth centering out of tight turns.",
        duration_seconds=150,
        video_url="https://assets.parivahan.internal/videos/academy/05_steering.mp4",
        tags=["steering", "wheel", "grip", "hand over hand", "push pull", "wheel centering"],
    ),
    AcademyVideo(
        video_id="vid_06_lane_change",
        topic="lane change",
        title="Safe Lane Changing & Blind Spot Checks",
        description="The Mirror-Signal-Manoeuvre (MSM) routine for highway and city lane transitions.",
        duration_seconds=175,
        video_url="https://assets.parivahan.internal/videos/academy/06_lane_change.mp4",
        tags=["lane change", "lane", "highway", "overtaking", "blind spot"],
    ),
    AcademyVideo(
        video_id="vid_07_parallel_parking",
        topic="parallel parking",
        title="Parallel Parking in 3 Easy Steps",
        description="Reference markers and curb alignment for tight roadside parallel parking.",
        duration_seconds=220,
        video_url="https://assets.parivahan.internal/videos/academy/07_parallel_parking.mp4",
        tags=["parallel parking", "parallel", "curb", "roadside parking"],
    ),
    AcademyVideo(
        video_id="vid_08_emergency_braking",
        topic="emergency braking",
        title="Emergency Braking & ABS Vehicle Control",
        description="Stopping firmly in the shortest distance while maintaining steering control.",
        duration_seconds=140,
        video_url="https://assets.parivahan.internal/videos/academy/08_emergency_braking.mp4",
        tags=["emergency braking", "brake", "stopping distance", "sudden stop", "abs"],
    ),
    AcademyVideo(
        video_id="vid_09_mirror_signal",
        topic="mirror and signal checks",
        title="Mirror Checks and Signalling Discipline",
        description="Interior and wing mirror scanning sequence and timely indicator usage before every manoeuvre.",
        duration_seconds=165,
        video_url="https://assets.parivahan.internal/videos/academy/09_mirror_signal.mp4",
        tags=["mirror and signal checks", "mirrors", "indicator", "signals", "blindspot"],
    ),
    AcademyVideo(
        video_id="vid_10_gradient_descent",
        topic="gradient descent",
        title="Downhill Driving & Engine Braking",
        description="Controlling vehicle descent on steep slopes using lower gears rather than riding the brakes.",
        duration_seconds=155,
        video_url="https://assets.parivahan.internal/videos/academy/10_gradient_descent.mp4",
        tags=["gradient descent", "downhill", "slope descent", "engine braking", "steep"],
    ),
]


def get_all_videos() -> list[AcademyVideo]:
    return ACADEMY_VIDEO_CATALOG


def get_video_by_id(video_id: str) -> AcademyVideo | None:
    for vid in ACADEMY_VIDEO_CATALOG:
        if vid.video_id == video_id:
            return vid
    return None


def get_video_by_topic(topic: str) -> AcademyVideo | None:
    norm_topic = topic.strip().lower()
    for vid in ACADEMY_VIDEO_CATALOG:
        if vid.topic.lower() == norm_topic:
            return vid
    return None
