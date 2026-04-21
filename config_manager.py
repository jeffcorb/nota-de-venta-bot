"""Gestión de la configuración del negocio en JSON local."""

import json
import os
from pathlib import Path


class ConfigManager:
    def __init__(self, config_path: str = None):
        if config_path is None:
            data_dir = os.environ.get("DATA_DIR", "data")
            config_path = f"{data_dir}/config.json"
        self.config_file = Path(config_path)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

    def get_config(self) -> dict | None:
        if not self.config_file.exists():
            return None
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_config(self, config: dict) -> None:
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

    def is_configured(self) -> bool:
        config = self.get_config()
        return config is not None and bool(config.get("nombre"))

    def update_logo(self, logo_url: str) -> None:
        config = self.get_config() or {}
        config["logo_url"] = logo_url
        self.save_config(config)

    def get_next_sale_number(self) -> int:
        config = self.get_config() or {}
        number = config.get("ultimo_numero", 0) + 1
        config["ultimo_numero"] = number
        self.save_config(config)
        return number
