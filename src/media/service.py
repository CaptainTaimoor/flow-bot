import os
import json
import shutil
import asyncio
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from src.config.settings import settings

logger = logging.getLogger(__name__)

class MediaService:
    def __init__(self):
        settings.ensure_directories()
        self.videos_dir = Path(settings.VIDEOS_DIR)
        self.thumbnails_dir = Path(settings.THUMBNAILS_DIR)

    def get_destination_video_path(self, job_id: int, generation_id: int) -> Path:
        filename = f"job_{job_id}_{generation_id}.mp4"
        return self.videos_dir / filename

    def get_destination_thumbnail_path(self, job_id: int, generation_id: int) -> Path:
        filename = f"thumb_{job_id}_{generation_id}.jpg"
        return self.thumbnails_dir / filename

    async def validate_video(self, video_path: str | Path) -> Tuple[bool, Dict[str, Any]]:
        """
        Deep validation of downloaded video media file using ffprobe.
        Validates container, video stream, codec, resolution, duration, and framerate.
        """
        path = Path(video_path)
        if not path.exists():
            return False, {"error": "File does not exist on disk"}

        file_size = path.stat().st_size
        if file_size == 0:
            return False, {"error": "File is completely empty (0 bytes)"}

        metadata: Dict[str, Any] = {
            "file_size": file_size,
            "duration": None,
            "width": None,
            "height": None,
            "video_codec": None,
            "audio_codec": None,
            "fps": None,
            "container": None,
            "ffprobe_metadata": None,
            "validation_method": "ffprobe",
        }

        # Check for ffprobe binary
        ffprobe_bin = shutil.which("ffprobe")
        if not ffprobe_bin:
            logger.warning("ffprobe not found on PATH. Falling back to basic file size verification.")
            metadata["validation_method"] = "basic_fallback"
            if file_size > 4096:
                return True, metadata
            return False, {"error": "File too small (<4KB) to be a valid video without ffprobe"}

        try:
            cmd = [
                ffprobe_bin,
                "-v", "error",
                "-show_format",
                "-show_streams",
                "-of", "json",
                str(path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                err_msg = stderr.decode("utf-8", errors="ignore").strip()
                logger.error(f"ffprobe validation failed: {err_msg}")
                return False, {"error": f"ffprobe validation failed: {err_msg}"}

            probe_data = json.loads(stdout.decode("utf-8"))
            metadata["ffprobe_metadata"] = probe_data

            streams = probe_data.get("streams", [])
            format_info = probe_data.get("format", {})

            # 1. Verify container format
            fmt_name = format_info.get("format_name", "")
            metadata["container"] = fmt_name
            if not any(c in fmt_name for c in ["mp4", "mov", "matroska", "webm", "quicktime"]):
                logger.warning(f"Unusual container format: {fmt_name}")

            # 2. Locate Video Stream
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
            if not video_stream:
                return False, {"error": "No video stream detected in file container"}

            metadata["video_codec"] = video_stream.get("codec_name")
            metadata["width"] = int(video_stream.get("width", 0))
            metadata["height"] = int(video_stream.get("height", 0))

            if metadata["width"] <= 0 or metadata["height"] <= 0:
                return False, {"error": f"Invalid video resolution: {metadata['width']}x{metadata['height']}"}

            # 3. Calculate FPS from frame rates
            r_fps = video_stream.get("r_frame_rate", "")
            if "/" in r_fps:
                num, den = r_fps.split("/")
                try:
                    if float(den) > 0:
                        metadata["fps"] = round(float(num) / float(den), 2)
                except Exception:
                    pass

            # 4. Locate Audio Stream (optional for video)
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
            if audio_stream:
                metadata["audio_codec"] = audio_stream.get("codec_name")

            # 5. Extract Duration
            dur_str = format_info.get("duration") or video_stream.get("duration")
            if dur_str:
                metadata["duration"] = round(float(dur_str), 2)

            if metadata["duration"] is not None and metadata["duration"] <= 0.2:
                return False, {"error": f"Video duration too short: {metadata['duration']}s"}

            logger.info(
                f"Video validated successfully: {metadata['width']}x{metadata['height']}, "
                f"codec={metadata['video_codec']}, duration={metadata['duration']}s, fps={metadata['fps']}"
            )
            return True, metadata

        except Exception as e:
            logger.exception(f"Exception during ffprobe validation: {e}")
            return False, {"error": f"Validation exception: {e}"}

    async def generate_thumbnail(
        self, video_path: str | Path, thumbnail_path: str | Path, duration: Optional[float] = None
    ) -> Optional[str]:
        """Generates a high-quality JPEG thumbnail using ffmpeg."""
        v_path = Path(video_path)
        t_path = Path(thumbnail_path)
        if not v_path.exists():
            return None

        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            logger.warning("ffmpeg not found on PATH. Thumbnail generation skipped.")
            return None

        t_path.parent.mkdir(parents=True, exist_ok=True)

        # Pick seek timestamp: 1.0s or halfway through short videos
        seek_time = "00:00:01.000"
        if duration and duration < 1.0:
            seek_time = f"00:00:00.{int(duration * 500):03d}"

        try:
            cmd = [
                ffmpeg_bin,
                "-y",
                "-ss", seek_time,
                "-i", str(v_path),
                "-vframes", "1",
                "-q:v", "2",
                str(t_path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()

            if proc.returncode == 0 and t_path.exists() and t_path.stat().st_size > 0:
                logger.info(f"Generated thumbnail successfully at {t_path}")
                return str(t_path)
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail via ffmpeg: {e}")

        return None

    def safe_resolve_media_path(self, file_path_str: str) -> Optional[Path]:
        """Ensures that requested file path stays strictly within allowed storage roots."""
        try:
            target = Path(file_path_str).resolve()
            allowed_roots = [
                Path(settings.DATA_DIR).resolve(),
                Path(settings.OUTPUT_DIR).resolve(),
                Path(settings.MEDIA_DIR).resolve(),
                Path(settings.VIDEOS_DIR).resolve(),
                Path(settings.THUMBNAILS_DIR).resolve(),
            ]
            for root in allowed_roots:
                if root in target.parents or target == root:
                    if target.exists() and target.is_file():
                        return target
        except Exception as e:
            logger.error(f"Path traversal safety check failed for '{file_path_str}': {e}")
        return None

media_service = MediaService()
