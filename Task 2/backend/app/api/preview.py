"""
preview.py — Live Detection Stream
====================================

MJPEG streaming endpoint for debugging the vision pipeline,
verifying face detection stability, and confirming system health
before calibration.
"""

import asyncio
import cv2
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.dependencies import tracker_service
from app.services.detector import detector_service # Kept for type hinting if needed
from app.utils.drawing import apply_overlays
from app.core.settings import settings
from app.models.tracker import TrackerStatus

router = APIRouter(tags=["Stream"])


async def generate_frames(mode: str):
    """
    Generator that retrieves the latest state from the TrackerService,
    applies overlays, and yields JPEG byte chunks.
    Avoids duplicate camera capture and MediaPipe processing.
    """
    while True:
        try:
            # 1. Retrieve cached state
            state = tracker_service.get_latest_state()
            
            raw_frame = state.frame
            if raw_frame is None:
                # If tracker hasn't captured a frame yet, just sleep
                await asyncio.sleep(0.1)
                continue

            # 2. Check Calibration Status visually
            is_calibrated = settings.CALIBRATION_FILE.exists()
            
            metrics = {
                "fps": state.fps,
                # We don't have per-frame inference ms here, but we could add it to TrackerState if needed
            }

            # 3. Extract Estimate values if available
            dist = state.estimate.distance if state.estimate else None
            angle = state.estimate.angle if state.estimate else None

            # 4. Draw
            annotated_frame = apply_overlays(
                frame=raw_frame,
                mode=mode,
                detection=state.detection,
                metrics=metrics,
                is_calibrated=is_calibrated,
                distance=dist,
                angle=angle
            )

            # 5. Encode
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), settings.JPEG_QUALITY]
            success, buffer = cv2.imencode('.jpg', annotated_frame, encode_param)
            if not success:
                continue

            # 6. Yield
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
            )
            
            # Stream at roughly 30 FPS maximum to the client
            await asyncio.sleep(0.033)

        except Exception as e:
            print(f"[Stream Error] {e}")
            break


@router.get(
    "/preview",
    summary="Live Detection Stream (MJPEG)",
    description="Streams real-time annotated camera feed for debugging and validation."
)
async def live_detection_stream(
    mode: str = Query("full", description="Overlay mode: full, bbox, measurements, raw")
):
    """Returns a continuous MJPEG stream of the camera feed."""
    return StreamingResponse(
        generate_frames(mode),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
