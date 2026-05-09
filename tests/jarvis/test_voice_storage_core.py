import tempfile
from pathlib import Path

import pytest

from jarvis.voice.storage import VoiceAudioStorage


def test_storage_init_does_not_create_dir_unittest_style():
    with tempfile.TemporaryDirectory() as td:
        base_dir = Path(td) / "voice_storage_base"

        VoiceAudioStorage(base_dir=base_dir)

        assert not base_dir.exists()


def test_storage_save_creates_dir_and_writes_file_unittest_style():
    with tempfile.TemporaryDirectory() as td:
        base_dir = Path(td) / "voice_storage_base"
        storage = VoiceAudioStorage(base_dir=base_dir)

        saved_path = Path(storage.save_audio(b"abc", "wav"))

        assert base_dir.exists()
        assert saved_path.exists()
        assert saved_path.parent == base_dir.resolve()


def test_storage_rejects_invalid_format_unittest_style():
    with tempfile.TemporaryDirectory() as td:
        storage = VoiceAudioStorage(base_dir=Path(td) / "voice_storage_base")
        with pytest.raises(ValueError, match="unsupported output_format"):
            storage.save_audio(b"abc", "flac")
