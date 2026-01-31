"""Image history storage for Z-Image web app.

Stores the last 20 generated images with metadata.
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger


@dataclass
class ImageRecord:
    """Metadata for a generated image."""

    id: str
    filename: str
    prompt: str
    style: str  # "anime" or "realistic"
    width: int
    height: int
    steps: int
    seed: int
    created_at: str
    generation_time: float  # seconds

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ImageRecord":
        return cls(**data)


class ImageStore:
    """Manages generated image history with persistence."""

    MAX_IMAGES = 20

    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.images_dir = storage_dir / "images"
        self.metadata_file = storage_dir / "history.json"

        # Ensure directories exist
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Load existing history
        self._history: list[ImageRecord] = []
        self._load_history()

    def _load_history(self) -> None:
        """Load history from disk."""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text())
                self._history = [ImageRecord.from_dict(r) for r in data]
                logger.info(f"Loaded {len(self._history)} images from history")
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
                self._history = []

    def _save_history(self) -> None:
        """Persist history to disk."""
        data = [r.to_dict() for r in self._history]
        self.metadata_file.write_text(json.dumps(data, indent=2))

    def add_image(
        self,
        image_path: Path,
        prompt: str,
        style: str,
        width: int,
        height: int,
        steps: int,
        seed: int,
        generation_time: float,
    ) -> ImageRecord:
        """Add a new image to the store."""
        record_id = str(uuid.uuid4())[:8]
        filename = f"{record_id}.png"
        dest_path = self.images_dir / filename

        # Copy image to store
        shutil.copy2(image_path, dest_path)

        record = ImageRecord(
            id=record_id,
            filename=filename,
            prompt=prompt,
            style=style,
            width=width,
            height=height,
            steps=steps,
            seed=seed,
            created_at=datetime.now().isoformat(),
            generation_time=generation_time,
        )

        # Add to front of history
        self._history.insert(0, record)

        # Trim to max size, removing oldest images
        while len(self._history) > self.MAX_IMAGES:
            old_record = self._history.pop()
            old_path = self.images_dir / old_record.filename
            if old_path.exists():
                old_path.unlink()
                logger.debug(f"Removed old image: {old_record.filename}")

        self._save_history()
        logger.info(f"Added image {record_id} to history")
        return record

    def get_history(self) -> list[ImageRecord]:
        """Get all images in history, newest first."""
        return list(self._history)

    def get_image(self, image_id: str) -> Optional[ImageRecord]:
        """Get a specific image by ID."""
        for record in self._history:
            if record.id == image_id:
                return record
        return None

    def get_image_path(self, image_id: str) -> Optional[Path]:
        """Get the file path for an image."""
        record = self.get_image(image_id)
        if record:
            return self.images_dir / record.filename
        return None

    def delete_image(self, image_id: str) -> bool:
        """Delete an image from the store. Returns True if successful."""
        record = self.get_image(image_id)
        if not record:
            return False

        # Remove file
        path = self.images_dir / record.filename
        if path.exists():
            path.unlink()

        # Remove from history
        self._history = [r for r in self._history if r.id != image_id]
        self._save_history()
        
        logger.info(f"Deleted image {image_id}")
        return True

    def clear(self) -> None:
        """Clear all history."""
        for record in self._history:
            path = self.images_dir / record.filename
            if path.exists():
                path.unlink()
        self._history = []
        self._save_history()
        logger.info("Cleared image history")
