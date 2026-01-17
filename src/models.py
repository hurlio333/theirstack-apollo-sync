from dataclasses import dataclass
from typing import Optional


@dataclass
class Company:
    """Represents a company record."""

    name: str
    domain: str
    source: str = "theirstack"
    discovered_at: Optional[str] = None

    def __post_init__(self):
        """Normalize domain on creation."""
        if self.domain:
            self.domain = self.domain.lower().strip()
            # Remove protocol if present
            if self.domain.startswith("http://"):
                self.domain = self.domain[7:]
            elif self.domain.startswith("https://"):
                self.domain = self.domain[8:]
            # Remove trailing slash
            self.domain = self.domain.rstrip("/")
