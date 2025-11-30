from pathlib import Path
from typing import Dict, Any
import tempfile
import json
import shutil
import subprocess
import os
from services.base import PDFConverter



# MinerU runs as a CLI in a separate venv, not imported as a Python module
MINERU_AVAILABLE = True


class MinerUConverter(PDFConverter):
    """Adapter for the MinerU CLI (requires mineru[core] installed in separate venv)."""

    def _get_mineru_bin(self) -> Path:
        """Get the path to the MinerU binary in the separate venv."""
        env_path = Path(os.environ.get("MINERU_ENV", "mineru_env"))
        return env_path / "bin" / "mineru"

    def __init__(self):
        """Initialize MinerU converter by checking if binary exists."""
        self._init_error = None
        # Check if the mineru binary exists in the separate venv
        mineru_bin = self._get_mineru_bin()
        if not mineru_bin.exists():
            self._init_error = f"MinerU binary not found at {mineru_bin}"

    @property
    def name(self) -> str:
        return "mineru"

    @property
    def available(self) -> bool:
        """MinerU is available if binary exists and no init errors occurred."""
        return MINERU_AVAILABLE and self._init_error is None

    @property
    def error_message(self) -> str:
        """Return error message if MinerU is not available."""
        if not MINERU_AVAILABLE:
            return "mineru not installed"
        if self._init_error:
            return f"MinerU initialization failed: {self._init_error}"
        return None

    def _run_mineru(self, file_path: str, output_dir: str) -> Dict[str, Any]:
        """Run MinerU CLI and return the output data."""
        cmd = ["mineru", "-p", file_path, "-o", output_dir, "--output-format", "json"]
        mineru_bin = self._get_mineru_bin()
        if mineru_bin.exists():
            cmd[0] = str(mineru_bin)
        subprocess.check_call(cmd)
        
        # MinerU may create nested directories, search recursively for auto directory
        output_path = Path(output_dir)
        auto_dirs = list(output_path.rglob("auto"))
        
        if not auto_dirs:
            raise RuntimeError(f"MinerU auto output directory not found in {output_dir}")
        
        # Use the first auto directory found
        auto_dir = auto_dirs[0]
        
        # Find the JSON file in the auto directory
        json_files = list(auto_dir.glob("*.json"))
        if not json_files:
            raise RuntimeError(f"No JSON output found in {auto_dir}")
        
        # Use the first JSON file found
        result_file = json_files[0]
        return json.loads(result_file.read_text())

    async def convert_to_md(self, file_path: str) -> str:
        """Convert PDF to Markdown using MinerU."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data = self._run_mineru(file_path, tmpdir)
        
        # Extract markdown content from MinerU output
        texts = []
        
        # Handle different data structures
        # 1. If data is directly a list, process it
        if isinstance(data, list):
            for entry in data:
                if isinstance(entry, dict):
                    # Try different markdown field names
                    markdown = entry.get("markdown") or entry.get("content") or entry.get("text", "")
                    if markdown:
                        texts.append(markdown)
        
        # 2. If data is a dict, try different structures
        elif isinstance(data, dict):
            # Try pages array first
            pages = data.get("pages", [])
            if pages and isinstance(pages, list):
                for entry in pages:
                    if isinstance(entry, dict):
                        markdown = entry.get("markdown") or entry.get("content") or entry.get("text", "")
                        if markdown:
                            texts.append(markdown)
            
            # If no pages or empty, try top-level markdown
            if not texts and data.get("markdown"):
                texts.append(data.get("markdown"))
            
            # If still empty, try to build from all available text fields
            if not texts:
                if data.get("content"):
                    texts.append(data.get("content"))
                elif data.get("text"):
                    texts.append(data.get("text"))
        
        result = "\n\n".join(texts).strip()
        return result

    async def convert_to_json(self, file_path: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as tmpdir:
            data = self._run_mineru(file_path, tmpdir)
        
        # Calculate total pages - handle both list and dict structures
        total_pages = 0
        if isinstance(data, list):
            # If data is a list, count unique page_idx values
            page_indices = set()
            for item in data:
                if isinstance(item, dict) and "page_idx" in item:
                    page_indices.add(item["page_idx"])
            total_pages = len(page_indices)
        elif isinstance(data, dict):
            total_pages = len(data.get("pages", []))
        
        return {
            "content": data,
            "format": "json",
            "library": self.name,
            "total_pages": total_pages
        }

    async def convert_to_text(self, file_path: str) -> str:
        markdown = await self.convert_to_md(file_path)
        clean = markdown.replace("#", "")
        return clean

