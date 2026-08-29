"""Driving Academy video catalog (Module 4).

Target: ~10 pre-generated instructional clips covering practical driving test skills.
Topics 1-5 explicitly named in Section 5.4; Topics 6-10 from Section 10.6.
Enriched with Hindi titles, Hinglish keywords, and thumbnail assets.
"""

from contracts.academy import AcademyVideo

ACADEMY_VIDEO_CATALOG: list[AcademyVideo] = [
    AcademyVideo(
        video_id="vid_01_eight_turn",
        topic="8-turn",
        title="Mastering the Figure-8 Driving Track",
        hindi_title="फिगर-8 ड्राइविंग ट्रैक पर कार चलाना सीखें",
        description="Master steering wheel hand-over-hand technique and track entry/exit reference points for the RTO 8-track test.",
        duration_seconds=185,
        video_url="/videos/eight_turn.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1541899481282-d53bffe3c35d?w=400",
        tags=[
            "8-turn",
            "8 turn",
            "8 track",
            "8-track",
            "figure 8",
            "figure-8",
            "eight turn",
            "eight track",
            "rto track",
            "test track",
            "आठ",
            "आठ ट्रैक",
        ],
        hinglish_keywords=[
            "8 banana",
            "aath track",
            "aath number",
            "figure 8 me steering",
            "eight track kaise pass kare",
            "rto test 8 track",
        ],
    ),
    AcademyVideo(
        video_id="vid_02_reverse_parking",
        topic="reverse parking",
        title="Flawless Reverse & Bay Parking",
        hindi_title="रिवर्स पार्किंग और बे पार्किंग का सही तरीका",
        description="Learn mirror alignment, 45-degree angle entry, and smooth reversing without touching track cones or curbs.",
        duration_seconds=210,
        video_url="/videos/reverse_parking.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1506521781263-d8422e82f27a?w=400",
        tags=[
            "reverse parking",
            "reverse",
            "parking",
            "cones",
            "bay parking",
            "s-track",
            "रिवर्स",
            "रिवर्स पार्किंग",
        ],
        hinglish_keywords=[
            "reverse kaise kare",
            "gaadi peeche lena",
            "reverse me gadi modna",
            "parking lagana",
            "cone se bachna",
        ],
    ),
    AcademyVideo(
        video_id="vid_03_hill_start",
        topic="hill start",
        title="Hill Start & Incline Control without Rollback",
        hindi_title="चढ़ाई / ढलान पर बिना पीछे खिसके गाड़ी उठाना",
        description="Coordinate handbrake and clutch biting point to take off smoothly uphill on the RTO incline ramp without rollback.",
        duration_seconds=195,
        video_url="/videos/hill_start.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=400",
        tags=[
            "hill start",
            "incline",
            "slope",
            "ramp",
            "rollback",
            "handbrake",
            "uphill",
            "ढलान",
            "चढ़ाई",
            "रैंप",
            "हैंडब्रेक",
        ],
        hinglish_keywords=[
            "chadhai par gadi",
            "incline pe rollback",
            "hill start handbrake",
            "gadi peeche ja rahi hai",
            "dhalaan pe uthana",
        ],
    ),
    AcademyVideo(
        video_id="vid_04_clutch_control",
        topic="clutch control",
        title="Finding the Clutch Biting Point & Anti-Stalling",
        hindi_title="क्लच बाइटिंग पॉइंट और गाड़ी बंद होने से बचाना",
        description="Prevent engine stalling in bumper-to-bumper traffic and master smooth clutch engagement and gear shifting.",
        duration_seconds=160,
        video_url="https://assets.parivahan.internal/videos/academy/04_clutch_control.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1489824904134-891ab64532f1?w=400",
        tags=[
            "clutch control",
            "clutch",
            "biting point",
            "stalling",
            "gear shift",
            "engine stall",
            "क्लच",
            "क्लच कंट्रोल",
        ],
        hinglish_keywords=[
            "clutch kaise chhodna",
            "gadi band ho jaati hai",
            "clutch biting point",
            "half clutch kaise use kare",
            "stalling problem",
        ],
    ),
    AcademyVideo(
        video_id="vid_05_steering",
        topic="steering",
        title="Steering Techniques: Push-Pull vs Hand-over-Hand",
        hindi_title="स्टीयरिंग व्हील पकड़ने और मोड़ने की तकनीक",
        description="Master 9-and-3 grip position, controlled push-pull turning, and smooth centering when exiting bends.",
        duration_seconds=150,
        video_url="https://assets.parivahan.internal/videos/academy/05_steering.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400",
        tags=[
            "steering",
            "wheel",
            "grip",
            "hand over hand",
            "push pull",
            "wheel centering",
            "स्टीयरिंग",
            "मोड़",
        ],
        hinglish_keywords=[
            "steering kaise pakde",
            "turn pe steering kitna kaate",
            "steering control",
            "wheel seedha kaise kare",
        ],
    ),
    AcademyVideo(
        video_id="vid_06_lane_change",
        topic="lane change",
        title="Safe Lane Changing & Blind Spot Checks",
        hindi_title="लेन बदलना और ब्लाइंड स्पॉट चेक करना",
        description="Follow the Mirror-Signal-Manoeuvre (MSM) routine for seamless and safe lane transitions on multi-lane roads.",
        duration_seconds=175,
        video_url="https://assets.parivahan.internal/videos/academy/06_lane_change.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1502877338535-766e1452684a?w=400",
        tags=[
            "lane change",
            "lane",
            "highway",
            "overtaking",
            "blind spot",
            "msm",
            "लेन",
            "ओवरटेक",
        ],
        hinglish_keywords=[
            "lane kaise change kare",
            "highway pe lane",
            "overtake karte samay",
            "blind spot dekhna",
        ],
    ),
    AcademyVideo(
        video_id="vid_07_parallel_parking",
        topic="parallel parking",
        title="Parallel Parking in 3 Easy Steps",
        hindi_title="सड़क किनारे पैरेलल पार्किंग का आसान तरीका",
        description="Learn side mirror markers, 45-degree pivot points, and curb alignment for tight roadside parallel parking.",
        duration_seconds=220,
        video_url="https://assets.parivahan.internal/videos/academy/07_parallel_parking.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1590674899484-d5640e854abe?w=400",
        tags=[
            "parallel parking",
            "parallel",
            "curb",
            "roadside parking",
            "पैरेलल पार्किंग",
            "सड़क किनारे",
        ],
        hinglish_keywords=[
            "parallel parking trick",
            "sadak kinare park karna",
            "do gadiyo ke beech me lagana",
        ],
    ),
    AcademyVideo(
        video_id="vid_08_emergency_braking",
        topic="emergency braking",
        title="Emergency Braking & ABS Vehicle Control",
        hindi_title="इमरजेंसी ब्रेक लगाना और एबीएस का उपयोग",
        description="Learn firm threshold braking, preventing wheel lockup, and maintaining steering control in unexpected road emergencies.",
        duration_seconds=140,
        video_url="https://assets.parivahan.internal/videos/academy/08_emergency_braking.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400",
        tags=[
            "emergency braking",
            "brake",
            "stopping distance",
            "sudden stop",
            "abs",
            "इमरजेंसी ब्रेक",
            "ब्रेक",
        ],
        hinglish_keywords=[
            "achanak break lagana",
            "emergency stop",
            "abs kaise kaam karta hai",
            "brake control",
        ],
    ),
    AcademyVideo(
        video_id="vid_09_mirror_signal",
        topic="mirror and signal checks",
        title="Mirror Checks and Signalling Discipline",
        hindi_title="मिरर स्कैनिंग और सही समय पर इंडिकेटर देना",
        description="The interior rear-view and wing mirror check cadence, timely indicator discipline, and shoulder checks.",
        duration_seconds=165,
        video_url="https://assets.parivahan.internal/videos/academy/09_mirror_signal.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1511919884226-fd3cad34687c?w=400",
        tags=[
            "mirror and signal checks",
            "mirrors",
            "indicator",
            "signals",
            "blindspot",
            "मिरर",
            "इंडिकेटर",
            "शीशा",
        ],
        hinglish_keywords=[
            "mirror kab dekhna",
            "indicator kab dena",
            "side mirror setting",
            "rear view mirror check",
        ],
    ),
    AcademyVideo(
        video_id="vid_10_gradient_descent",
        topic="gradient descent",
        title="Downhill Driving & Engine Braking",
        hindi_title="ढलान से नीचे उतरते समय इंजन ब्रेकिंग का उपयोग",
        description="Use lower gear engine braking instead of riding the foot brake to prevent brake fade on long downhill slopes.",
        duration_seconds=155,
        video_url="https://assets.parivahan.internal/videos/academy/10_gradient_descent.mp4",
        thumbnail_url="https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=400",
        tags=[
            "gradient descent",
            "downhill",
            "slope descent",
            "engine braking",
            "steep",
            "ढलान उतरना",
            "इंजन ब्रेकिंग",
        ],
        hinglish_keywords=[
            "dhalaan se utarna",
            "engine brake kaise use kare",
            "gear me dhalan utarna",
            "brake garam hona",
        ],
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
