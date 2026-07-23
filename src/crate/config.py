from __future__ import annotations

import tomllib
from dataclasses import dataclass, asdict
from pathlib import Path

import tomli_w

DEFAULT_CONFIG_PATH = Path("~/.config/crate/config.toml").expanduser()
_DEFAULT_LIBRARY_ROOT = "~/Desktop/crate"


@dataclass
class Config:
    library_root: Path
    default_preset: str = "sample"
    sample_format: str = "wav"
    normalize: bool = False
    filename_template: str = "%(title)s"

    @classmethod
    def defaults(cls) -> "Config":
        return cls(library_root=Path(_DEFAULT_LIBRARY_ROOT).expanduser())


def load_config(path: Path | None = None) -> Config:
    path = path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return Config.defaults()
    data = tomllib.loads(path.read_text())
    root = data.get("library_root", _DEFAULT_LIBRARY_ROOT)
    return Config(
        library_root=Path(root).expanduser(),
        default_preset=data.get("default_preset", "sample"),
        sample_format=data.get("sample_format", "wav"),
        normalize=data.get("normalize", False),
        filename_template=data.get("filename_template", "%(title)s"),
    )


def save_config(cfg: Config, path: Path | None = None) -> None:
    path = path or DEFAULT_CONFIG_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(cfg)
    data["library_root"] = str(cfg.library_root)
    path.write_text(tomli_w.dumps(data))
