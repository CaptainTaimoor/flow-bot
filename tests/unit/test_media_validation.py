import os
import pytest
from pathlib import Path
from src.media.service import media_service

@pytest.mark.asyncio
async def test_validate_existing_video():
    video_path = Path("data/media/videos/flow_generation_job_1.mp4")
    if not video_path.exists():
        pytest.skip("Test video file not present")

    is_valid, meta = await media_service.validate_video(video_path)
    assert is_valid is True
    assert meta["width"] is not None and meta["width"] > 0
    assert meta["height"] is not None and meta["height"] > 0
    assert meta["duration"] is not None and meta["duration"] > 0
    assert meta["video_codec"] is not None
    assert meta["file_size"] > 1000

@pytest.mark.asyncio
async def test_validate_nonexistent_file():
    is_valid, meta = await media_service.validate_video("non_existent_file.mp4")
    assert is_valid is False
    assert "not exist" in meta["error"]

@pytest.mark.asyncio
async def test_validate_empty_file(tmp_path):
    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"")

    is_valid, meta = await media_service.validate_video(empty_file)
    assert is_valid is False
    assert "empty" in meta["error"]

@pytest.mark.asyncio
async def test_thumbnail_generation(tmp_path):
    video_path = Path("data/media/videos/flow_generation_job_1.mp4")
    if not video_path.exists():
        pytest.skip("Test video file not present")

    thumb_dest = tmp_path / "test_thumb.jpg"
    thumb_path = await media_service.generate_thumbnail(video_path, thumb_dest)
    assert thumb_path is not None
    assert os.path.exists(thumb_path)
    assert os.path.getsize(thumb_path) > 500

def test_safe_resolve_media_path():
    # Should resolve valid media path within data dir
    valid_path = str(Path("data/media/videos/flow_generation_job_1.mp4").resolve())
    resolved = media_service.safe_resolve_media_path(valid_path)
    assert resolved is not None

    # Path traversal attempt should return None
    traversal_path = "data/../../Windows/System32/drivers/etc/hosts"
    assert media_service.safe_resolve_media_path(traversal_path) is None
