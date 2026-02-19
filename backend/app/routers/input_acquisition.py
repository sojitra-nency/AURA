"""
FastAPI endpoints for the Input Acquisition layer.

Exposes the InputAcquisitionManager over HTTP.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.input_acquisition.manager import InputAcquisitionManager
from app.input_acquisition.time_manager import TimeManager, TimeMode
from app.input_acquisition.buffer import InputBuffer
from app.input_acquisition.logger import InputLogger
from app.input_acquisition.validation import ValidationError

router = APIRouter(prefix="/api/input", tags=["input-acquisition"])

# Shared singleton — created once, persists for server lifetime
_time_mgr = TimeManager(mode=TimeMode.REAL)
_buffer = InputBuffer(capacity=5000)
_logger = InputLogger()
_manager = InputAcquisitionManager(
    time_manager=_time_mgr,
    buffer=_buffer,
    logger=_logger,
    session_id="api-session",
)


def get_manager() -> InputAcquisitionManager:
    return _manager


# --- Request schemas ---


class TextPayload(BaseModel):
    text: str = Field(..., min_length=1)
    source_id: str = "api"
    metadata: dict | None = None


class AudioPayload(BaseModel):
    waveform: list[float]
    sample_rate: int = Field(..., gt=0)
    channels: int = Field(1, gt=0)
    source_id: str = "api"
    metadata: dict | None = None


class VideoPayload(BaseModel):
    frames: list
    resolution: list[int] = Field(..., min_length=2, max_length=2)
    source_id: str = "api"
    metadata: dict | None = None


class PhysiologicalPayload(BaseModel):
    signals: dict[str, list[float]]
    signal_type: str = Field(..., min_length=1)
    sampling_frequency: float = Field(..., gt=0)
    source_id: str = "api"
    metadata: dict | None = None


# --- Endpoints ---


@router.post("/text")
async def receive_text(payload: TextPayload):
    try:
        inp = _manager.receive_text(
            text=payload.text,
            source_id=payload.source_id,
            metadata=payload.metadata,
        )
        return {"id": inp.id, "modality": inp.modality, "timestamp": inp.timestamp}
    except (ValidationError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/audio")
async def receive_audio(payload: AudioPayload):
    try:
        inp = _manager.receive_audio(
            waveform=payload.waveform,
            sample_rate=payload.sample_rate,
            channels=payload.channels,
            source_id=payload.source_id,
            metadata=payload.metadata,
        )
        return {"id": inp.id, "modality": inp.modality, "timestamp": inp.timestamp}
    except (ValidationError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/video")
async def receive_video(payload: VideoPayload):
    try:
        inp = _manager.receive_video(
            frames=payload.frames,
            resolution=tuple(payload.resolution),
            source_id=payload.source_id,
            metadata=payload.metadata,
        )
        return {"id": inp.id, "modality": inp.modality, "timestamp": inp.timestamp}
    except (ValidationError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/physiological")
async def receive_physiological(payload: PhysiologicalPayload):
    try:
        inp = _manager.receive_physiological(
            signal_dict=payload.signals,
            signal_type=payload.signal_type,
            sampling_frequency=payload.sampling_frequency,
            source_id=payload.source_id,
            metadata=payload.metadata,
        )
        return {"id": inp.id, "modality": inp.modality, "timestamp": inp.timestamp}
    except (ValidationError, ValueError, TypeError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/latest")
async def get_latest(n: int = 5):
    items = _manager.get_latest(n)
    return [i.to_dict() for i in items]


@router.get("/all")
async def get_all():
    items = _manager.get_all()
    return [i.to_dict() for i in items]


@router.get("/by-modality/{modality}")
async def get_by_modality(modality: str):
    items = _manager.get_by_modality(modality)
    return [i.to_dict() for i in items]


@router.get("/by-id/{input_id}")
async def get_by_id(input_id: str):
    item = _manager.get_by_id(input_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Input not found")
    return item.to_dict()


@router.get("/replay")
async def replay():
    items = _manager.replay()
    return [i.to_dict() for i in items]


@router.get("/stats")
async def stats():
    return _manager.stats()


@router.delete("/buffer")
async def clear_buffer():
    _manager.clear_buffer()
    return {"status": "buffer cleared"}
