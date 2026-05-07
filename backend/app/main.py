from __future__ import annotations

import asyncio
import os
import shlex
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", str(DEFAULT_ROOT))).resolve()
MAX_LOG_CHARS = 60_000


TASKS: dict[str, dict[str, Any]] = {
    "pdf_resize_cropmarks": {
        "script": "pdf.py",
        "category": "pdf",
        "input_mode": "stdin",
        "supports_container": True,
        "requires_display": False,
        "description": "Resize each page to trim size and draw crop marks.",
        "notes": [
            "Pass the input PDF path as stdin, example: 01.pdf",
            "Output is generated as *_work.pdf next to source file",
        ],
        "example": {"args": [], "stdin": "01.pdf\n"},
    },
    "pdf_resize_lambda_variant": {
        "script": "main.py",
        "category": "pdf",
        "input_mode": "module",
        "supports_container": True,
        "requires_display": False,
        "description": "AWS Lambda oriented PDF processor sample.",
        "notes": [
            "Designed for lambda_handler, not direct CLI script",
            "Use as reference or adapt to dedicated service endpoint",
        ],
        "example": {"args": []},
    },
    "screen_capture_hotkey": {
        "script": "cap.py",
        "category": "video",
        "input_mode": "args",
        "supports_container": False,
        "requires_display": True,
        "description": "Desktop screen recording via global hotkeys.",
        "notes": [
            "Requires desktop GUI and keyboard hooks",
            "Produces z_YYYYmmdd_HHMMSS.mp4",
        ],
        "example": {"args": []},
    },
    "video_caption_tts": {
        "script": "ana.py",
        "category": "video-ai",
        "input_mode": "args",
        "supports_container": True,
        "requires_display": False,
        "description": "BLIP captioning + subtitle burn-in + TTS merge.",
        "notes": [
            "Recommended args: <video_path> --frame-interval 2",
            "Requires model download and FFmpeg",
        ],
        "example": {"args": ["z_20260301_120000.mp4", "--frame-interval", "2"]},
    },
    "capture_then_analyze": {
        "script": "main2.py",
        "category": "pipeline",
        "input_mode": "args",
        "supports_container": False,
        "requires_display": True,
        "description": "Runs cap.py then executes ana.py on latest output.",
        "notes": [
            "Desktop capture dependency inherited from cap.py",
            "Useful for local interactive workflow",
        ],
        "example": {"args": []},
    },
    "mask_jumin_ocr": {
        "script": "mask.py",
        "category": "ocr",
        "input_mode": "args",
        "supports_container": True,
        "requires_display": False,
        "description": "Detect and mask Korean ID patterns in images.",
        "notes": [
            "Default folders are org/ -> upd/",
            "Ensure Tesseract executable/data path is configured",
        ],
        "example": {"args": []},
    },
    "subtitle_remove_experiment": {
        "script": "remove.py",
        "category": "video",
        "input_mode": "args",
        "supports_container": True,
        "requires_display": False,
        "description": "Frame inpainting experiment for subtitle removal.",
        "notes": [
            "Input is hard-coded as 1.mp4",
            "Writes frames/, cleaned_frames/, output_cleaned.mp4",
        ],
        "example": {"args": []},
    },
    "capture_with_static_tts": {
        "script": "start.py",
        "category": "video",
        "input_mode": "args",
        "supports_container": False,
        "requires_display": True,
        "description": "Screen capture and static TTS post-processing.",
        "notes": [
            "Requires desktop GUI and keyboard hooks",
            "Generates record_*.mp4 and final_record_*.mp4",
        ],
        "example": {"args": []},
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_within(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def resolve_script(task_id: str) -> Path:
    script_rel: str = TASKS[task_id]["script"]
    script_path = (WORKSPACE_ROOT / script_rel).resolve()
    if not is_within(script_path, WORKSPACE_ROOT):
        raise HTTPException(status_code=400, detail="Invalid script path.")
    if not script_path.exists():
        raise HTTPException(status_code=404, detail=f"Script not found: {script_rel}")
    return script_path


def resolve_cwd(raw_cwd: str) -> Path:
    raw_path = Path(raw_cwd)
    cwd_path = (WORKSPACE_ROOT / raw_path).resolve() if not raw_path.is_absolute() else raw_path.resolve()
    if not is_within(cwd_path, WORKSPACE_ROOT):
        raise HTTPException(status_code=400, detail="cwd must be under workspace root.")
    if not cwd_path.exists() or not cwd_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Invalid cwd: {raw_cwd}")
    return cwd_path


def trim_log(text: str) -> str:
    if len(text) <= MAX_LOG_CHARS:
        return text
    return text[-MAX_LOG_CHARS:]


class TaskInfo(BaseModel):
    id: str
    script: str
    category: str
    input_mode: str
    supports_container: bool
    requires_display: bool
    description: str
    notes: list[str] = Field(default_factory=list)
    example: dict[str, Any] = Field(default_factory=dict)


class JobCreateRequest(BaseModel):
    task_id: str = Field(..., description="Task id from /api/tasks")
    args: list[str] = Field(default_factory=list, description="CLI args forwarded to script")
    stdin: str | None = Field(default=None, description="Optional stdin payload")
    cwd: str = Field(default=".", description="Working directory under workspace root")


class JobInfo(BaseModel):
    id: str
    task_id: str
    command: list[str]
    cwd: str
    status: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""


app = FastAPI(
    title="pycap automation backend",
    version="0.1.0",
    description="FastAPI facade for script-based automation tasks in this repository.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: dict[str, dict[str, Any]] = {}


def serialize_task(task_id: str, spec: dict[str, Any]) -> TaskInfo:
    return TaskInfo(
        id=task_id,
        script=spec["script"],
        category=spec["category"],
        input_mode=spec["input_mode"],
        supports_container=spec["supports_container"],
        requires_display=spec["requires_display"],
        description=spec["description"],
        notes=spec.get("notes", []),
        example=spec.get("example", {}),
    )


async def execute_job(job_id: str) -> None:
    job = JOBS[job_id]
    stdin_payload = job.get("stdin")
    job["status"] = "running"
    job["started_at"] = now_iso()

    try:
        proc = await asyncio.create_subprocess_exec(
            *job["command"],
            cwd=job["cwd"],
            stdin=asyncio.subprocess.PIPE if stdin_payload is not None else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdin_bytes = stdin_payload.encode("utf-8") if stdin_payload is not None else None
        stdout, stderr = await proc.communicate(stdin_bytes)

        job["return_code"] = proc.returncode
        job["stdout"] = trim_log(stdout.decode("utf-8", errors="replace"))
        job["stderr"] = trim_log(stderr.decode("utf-8", errors="replace"))
        job["status"] = "succeeded" if proc.returncode == 0 else "failed"
    except Exception as exc:  # pragma: no cover - runtime protection
        job["status"] = "failed"
        job["stderr"] = trim_log(f"{job.get('stderr', '')}\n{exc}")
    finally:
        job["finished_at"] = now_iso()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "time": now_iso()}


@app.get("/api/tasks", response_model=list[TaskInfo])
def list_tasks() -> list[TaskInfo]:
    return [serialize_task(task_id, spec) for task_id, spec in TASKS.items()]


@app.post("/api/jobs", response_model=JobInfo, status_code=202)
async def create_job(req: JobCreateRequest) -> JobInfo:
    if req.task_id not in TASKS:
        raise HTTPException(status_code=404, detail=f"Unknown task_id: {req.task_id}")

    script_path = resolve_script(req.task_id)
    cwd_path = resolve_cwd(req.cwd)
    python_exec = os.getenv("PYTHON_EXECUTABLE", sys.executable)
    command = [python_exec, str(script_path), *req.args]

    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "task_id": req.task_id,
        "command": command,
        "cwd": str(cwd_path),
        "status": "queued",
        "created_at": now_iso(),
        "started_at": None,
        "finished_at": None,
        "return_code": None,
        "stdout": "",
        "stderr": "",
        "stdin": req.stdin,
    }
    JOBS[job_id] = job
    asyncio.create_task(execute_job(job_id))
    return JobInfo(**job)


@app.get("/api/jobs", response_model=list[JobInfo])
def list_jobs() -> list[JobInfo]:
    jobs = sorted(JOBS.values(), key=lambda item: item["created_at"], reverse=True)
    return [JobInfo(**job) for job in jobs]


@app.get("/api/jobs/{job_id}", response_model=JobInfo)
def get_job(job_id: str) -> JobInfo:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobInfo(**job)


@app.get("/api/jobs/{job_id}/command")
def get_job_command(job_id: str) -> dict[str, str]:
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {"command": shlex.join(job["command"])}
