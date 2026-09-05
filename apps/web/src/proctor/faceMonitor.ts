// Real on-device face monitoring for the proctored exam.
//
// MediaPipe BlazeFace runs entirely in the browser (model + wasm are vendored
// under /proctor/, so no frame, embedding, or image ever leaves the device —
// only event counts appear in the integrity report). Degradation ladder:
//   full  → detector running, face count is real
//   basic → camera on but the model failed to load; presence not analysed
//   off   → camera denied/unavailable; exam continues, tier capped at review

import type { FaceDetector } from "@mediapipe/tasks-vision";

export type FaceMode = "full" | "basic" | "off";

export interface FaceStatus {
  mode: FaceMode;
  faces: number | null; // null when not analysable
}

export class FaceMonitor {
  private detector: FaceDetector | null = null;
  private timer: ReturnType<typeof setInterval> | null = null;
  mode: FaceMode = "off";

  async start(
    video: HTMLVideoElement,
    onStatus: (status: FaceStatus) => void,
    intervalMs = 1600,
  ): Promise<FaceMode> {
    try {
      // Lazy-loaded: the vision bundle (~150KB) ships only when an exam starts.
      const { FaceDetector, FilesetResolver } = await import("@mediapipe/tasks-vision");
      const fileset = await FilesetResolver.forVisionTasks("/proctor/wasm");
      this.detector = await FaceDetector.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: "/proctor/blaze_face_short_range.tflite" },
        runningMode: "VIDEO",
        minDetectionConfidence: 0.5,
      });
      this.mode = "full";
    } catch {
      this.detector = null;
      this.mode = "basic";
    }

    if (this.mode === "full") {
      this.timer = setInterval(() => {
        if (!this.detector || video.readyState < 2) return;
        try {
          const result = this.detector.detectForVideo(video, performance.now());
          onStatus({ mode: "full", faces: result.detections.length });
        } catch {
          onStatus({ mode: "basic", faces: null });
        }
      }, intervalMs);
    } else {
      onStatus({ mode: this.mode, faces: null });
    }
    return this.mode;
  }

  stop(): void {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    this.detector?.close();
    this.detector = null;
  }
}
