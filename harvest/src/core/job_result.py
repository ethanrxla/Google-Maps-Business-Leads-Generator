from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class HarvestJobResult:
    domain: str
    sources: List[str]
    limit: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str  # "success" | "error"
    raw_output_path: Optional[str]
    error_message: Optional[str] = None
    parsed_data: Optional[Dict[str, Any]] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
