"""
Local storage service for handling document uploads and retrieval.
Stores files locally in an output directory and serves as primary storage.
"""
from __future__ import annotations

import os
import logging
import hashlib
from pathlib import Path
from typing import Tuple, Dict, Optional

import aiofiles
from fastapi import UploadFile

from utils.generate_id import generate_id  # keep your existing generator

# Configure logging once here (or in your app's entrypoint)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class LocalStorageService:
    """
    A filesystem-backed storage service.
    - Streams uploads to avoid loading the entire file into memory.
    - Writes to a temporary path and atomically moves into place on success.
    - Stores simple metadata alongside the file.
    """

    # Allow-list (optional): set to None to allow any extension
    ALLOWED_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".txt", ".docx", ".csv", ".json"}
    MAX_UPLOAD_MB = 100  # adjust as needed

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize local storage service with output directory.
        If not provided, uses:
        - ENV OUTPUT_DIR, else
        - <project_root>/outputs
        """
        if output_dir:
            base = Path(output_dir)
        else:
            env_dir = os.getenv("OUTPUT_DIR")
            if env_dir:
                base = Path(env_dir)
            else:
                # project_root = <repo>/.../this_file/../../
                project_root = Path(__file__).resolve().parents[1]
                base = project_root / "outputs"

        self.output_dir = base.resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorageService initialized with output_dir: {self.output_dir}")

        # Size guard (in bytes)
        self._max_bytes = self.MAX_UPLOAD_MB * 1024 * 1024

    async def upload_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Store a file locally in the outputs directory.

        Args:
            file: The uploaded file object

        Returns:
            tuple: (file_id, filepath) where file_id is the unique ID and filepath is the path to the stored file
        """
        if not file or not getattr(file, "filename", ""):
            raise ValueError("No file provided or filename missing.")

        # Generate ID & make per-file folder
        file_id = generate_id()
        file_dir = self.output_dir / file_id
        file_dir.mkdir(parents=True, exist_ok=True)

        # Resolve extension & optionally enforce allow-list
        orig_name = file.filename
        _, ext = os.path.splitext(orig_name or "")
        ext = ext.lower() or ".bin"
        if self.ALLOWED_EXTS is not None and ext not in self.ALLOWED_EXTS:
            raise ValueError(f"Unsupported file type: {ext}")

        # Paths
        final_path = file_dir / f"document{ext}"
        tmp_path = file_dir / f".document{ext}.part"
        meta_path = file_dir / "metadata.txt"

        logger.info(f"Saving uploaded file to temporary path: {tmp_path}")

        # Stream to disk with a hash + size counter
        h = hashlib.sha256()
        total = 0
        chunk_size = 1024 * 1024  # 1 MiB

        try:
            async with aiofiles.open(tmp_path, "wb") as out:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > self._max_bytes:
                        logger.warning(
                            "Upload aborted: size %s exceeds limit %s bytes",
                            total,
                            self._max_bytes,
                        )
                        # Best-effort cleanup handled below
                        raise ValueError("File too large.")
                    h.update(chunk)
                    await out.write(chunk)

            # Atomic move into place
            tmp_path.replace(final_path)

            # Write metadata
            async with aiofiles.open(meta_path, "w") as m:
                await m.write(f"Original filename: {orig_name}\n")
                await m.write(f"Content type: {getattr(file, 'content_type', '')}\n")
                await m.write(f"Saved path: {str(final_path)}\n")
                await m.write(f"Size (bytes): {total}\n")
                await m.write(f"SHA256: {h.hexdigest()}\n")

            logger.info("File uploaded successfully with ID: %s -> %s", file_id, final_path)
            return file_id, str(final_path)

        except Exception:
            logger.exception("Upload failed")
            # Cleanup temp file if present
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except Exception:
                logger.exception("Failed to clean up temp file")
            raise

    def get_file_path(self, file_id: str) -> str:
        """
        Get the file path for a specific file ID.

        Args:
            file_id: The unique file ID

        Returns:
            str: The path to the file
        """
        file_dir = self.output_dir / file_id
        if not file_dir.exists():
            logger.error("File directory not found: %s", file_dir)
            raise FileNotFoundError(f"No file found with ID: {file_id}")

        # Find "document.*"
        for p in file_dir.glob("document.*"):
            return str(p)

        logger.error("No document file found in directory: %s", file_dir)
        raise FileNotFoundError(f"No document file found in directory: {file_dir}")

    def get_metadata(self, file_id: str) -> Dict[str, str]:
        """
        Get metadata for a specific file ID.

        Args:
            file_id: The unique file ID

        Returns:
            dict: The metadata for the file
        """
        meta_path = self.output_dir / file_id / "metadata.txt"
        if not meta_path.exists():
            logger.error("Metadata file not found: %s", meta_path)
            return {}

        metadata: Dict[str, str] = {}
        with meta_path.open("r") as f:
            for line in f:
                if ":" in line:
                    key, value = line.strip().split(":", 1)
                    metadata[key.strip()] = value.strip()
        return metadata


# Create singleton instance (keeps your previous import style working)
local_storage_service = LocalStorageService()
