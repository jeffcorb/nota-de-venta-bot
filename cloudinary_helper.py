"""Integración con Cloudinary para almacenar el logo y la configuración del negocio."""

import json
import os
import cloudinary
import cloudinary.api
import cloudinary.uploader
import requests


class CloudinaryHelper:
    def __init__(self):
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            secure=True,
        )

    def is_configured(self) -> bool:
        return all(
            [
                os.getenv("CLOUDINARY_CLOUD_NAME"),
                os.getenv("CLOUDINARY_API_KEY"),
                os.getenv("CLOUDINARY_API_SECRET"),
            ]
        )

    def upload_logo(self, image_data: bytes) -> str:
        """Sube el logo a Cloudinary y devuelve la URL segura."""
        result = cloudinary.uploader.upload(
            image_data,
            public_id="logo",
            folder="nota_venta",
            overwrite=True,
            resource_type="image",
        )
        return result["secure_url"]

    def upload_config(self, config: dict) -> None:
        """Guarda la configuración del negocio en Cloudinary como JSON."""
        config_bytes = json.dumps(config, ensure_ascii=False, indent=2).encode("utf-8")
        cloudinary.uploader.upload(
            config_bytes,
            public_id="config",
            folder="nota_venta",
            overwrite=True,
            resource_type="raw",
        )

    def download_config(self) -> dict | None:
        """Descarga la configuración del negocio desde Cloudinary."""
        try:
            result = cloudinary.api.resource("nota_venta/config", resource_type="raw")
            resp = requests.get(result["secure_url"], timeout=10)
            return json.loads(resp.text)
        except Exception:
            return None
