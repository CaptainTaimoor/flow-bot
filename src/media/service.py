import os
import json
import shutil
import asyncio
import logging
import subprocess
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
        Validates the video file using ffprobe where available,
        with robust basic file system fallbacks.
        """
        path = Path(video_path)
        if not path.exists():
            return False, {"error": "File does not exist"}

        file_size = path.stat().st_size
        if file_size == 0:
            return False, {"error": "File is empty (0 bytes)"}

        metadata: Dict[str, Any] = {
            "file_size": file_size,
            "duration": None,
            "width": None,
            "height": None,
            "codec": None,
        }

        # Check if ffprobe is installed and available
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration,size:stream=width,height,codec_name,codec_type",
                "-of", "json",
                str(path),
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0:
                data = json.loads(stdout.decode("utf-8"))
                streams = data.get("streams", [])
                video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
                if video_stream:
                    metadata["width"] = video_stream.get("width")
                    metadata["height"] = video_stream.get("height")
                    metadata["codec"] = video_stream.get("codec_name")

                fmt = data.get("format", {})
                dur_str = fmt.get("duration")
                if dur_str:
                    metadata["duration"] = float(dur_str)

                return True, metadata
            else:
                logger.warning(f"ffprobe returned non-zero code: {stderr.decode('utf-8')}")
        except FileNotFoundError:
            logger.info("ffprobe not available on system, falling back to basic file checks.")
        except Exception as e:
            logger.warning(f"ffprobe validation error: {e}")

        # Basic fallback validation
        if file_size > 1024:  # At least 1KB
            return True, metadata
        return False, {"error": "File too small to be valid video"}

    async def generate_thumbnail(self, video_path: str | Path, thumbnail_path: str | Path) -> Optional[str]:
        """Generates a JPEG thumbnail using ffmpeg."""
        v_path = Path(video_path)
        t_path = Path(thumbnail_path)
        if not v_path.exists():
            return None

        t_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", "00:00:01.000",
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
                logger.info(f"Generated thumbnail at {t_path}")
                return str(t_path)
        except FileNotFoundError:
            logger.info("ffmpeg not available for thumbnail extraction.")
        except Exception as e:
            logger.warning(f"Failed to generate thumbnail: {e}")

        return None

    def safe_resolve_media_path(self, file_path_str: str) -> Optional[Path]:
        """Ensures that requested file path stays strictly within allowed media storage."""
        try:
            target = Path(file_path_str).resolve()
            media_root = Path(settings.DATA_DIR).resolve()
            output_root = Path(settings.OUTPUT_DIR).resolve()
            # Must reside within data or output directory
            if media_root in target.parents or output_root in target.parents or target == media_root:
                if target.exists() and target.is_file():
                    return target
        except Exception as e:
            logger.error(f"Security check failed for path '{file_path_str}': {e}")
        return None

media_service = MediaService()
