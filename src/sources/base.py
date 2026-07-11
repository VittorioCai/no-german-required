"""Job model and source interface."""
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str            # stable unique id, e.g. "greenhouse:n26:7742395"
    title: str
    company: str
    location: str
    url: str
    description: str   # plain text (HTML stripped)
    source: str
    tags: list = field(default_factory=list)
    country: str = ""  # "DE" if the source is Germany-only (skips geo check)


class Source:
    """Subclass and implement fetch() -> list[Job]. Failures must not crash the run."""

    name = "base"

    def fetch(self) -> list:
        raise NotImplementedError
