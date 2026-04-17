"""Integración con Cloudinary para almacenar el logo del negocio."""

import os
import cloudinary
import cloudinary.uploader


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
