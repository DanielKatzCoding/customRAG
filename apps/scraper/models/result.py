from dataclasses import dataclass, field


@dataclass
class ParseResult:
    content: list[str] = field(default_factory=list)
    extras: dict[str, list[str]] = field(default_factory=dict)

    @property
    def is_empty(self) -> bool:
        return not self.content and not self.extras
