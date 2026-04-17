# Bot de Notas de Venta en PDF

Bot de Telegram que genera notas de venta profesionales en PDF de forma conversacional, paso a paso.

## Características

- Configuración del negocio (nombre, teléfono, email, moneda)
- Logo almacenado en Cloudinary (se sube una sola vez)
- Flujo guiado para ingresar datos del cliente y artículos
- Múltiples artículos con cálculo automático de subtotales y total
- Notas y observaciones opcionales
- PDF profesional con logo, colores corporativos y tabla de productos
- Numeración automática de notas de venta
- Configuración guardada en JSON local

---

## Requisitos previos

- Python 3.11 o superior
- Cuenta en [Telegram](https://telegram.org) para crear el bot con [@BotFather](https://t.me/BotFather)
- Cuenta gratuita en [Cloudinary](https://cloudinary.com) para el logo

---

## Instalación local

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd NotadeVenta
```

### 2. Crear el entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

pip install -r requirements.txt
```

### 3. Crear el archivo `.env`

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales reales:

```env
TELEGRAM_BOT_TOKEN=123456789:AABBCCDDEEFFaabbccddeeff-gghhiijj
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret
```

#### Obtener el token de Telegram

1. Abre Telegram y busca **@BotFather**
2. Escribe `/newbot`
3. Sigue las instrucciones (nombre y username del bot)
4. BotFather te dará un token — cópialo en `TELEGRAM_BOT_TOKEN`

#### Obtener las credenciales de Cloudinary

1. Regístrate en [cloudinary.com](https://cloudinary.com) (plan gratuito disponible)
2. Ve al **Dashboard**
3. Copia los valores de **Cloud Name**, **API Key** y **API Secret**

### 4. Ejecutar el bot

```bash
python bot.py
```

---

## Despliegue en Railway

[Railway](https://railway.app) es la forma más sencilla de mantener el bot corriendo 24/7 de forma gratuita.

### Paso 1 — Preparar el repositorio

Sube el proyecto a GitHub:

```bash
git init
git add .
git commit -m "Bot de Notas de Venta"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```

> Asegúrate de que `.gitignore` excluye el archivo `.env` y `data/config.json`.

### Paso 2 — Crear proyecto en Railway

1. Ingresa a [railway.app](https://railway.app) y crea una cuenta (puedes usar GitHub)
2. Haz clic en **New Project → Deploy from GitHub repo**
3. Selecciona tu repositorio

### Paso 3 — Configurar variables de entorno

En Railway, ve a tu servicio → pestaña **Variables** → **New Variable** y agrega:

| Variable | Valor |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Tu token de BotFather |
| `CLOUDINARY_CLOUD_NAME` | Tu cloud name |
| `CLOUDINARY_API_KEY` | Tu API key |
| `CLOUDINARY_API_SECRET` | Tu API secret |

### Paso 4 — Crear el archivo `Procfile`

Railway necesita saber cómo arrancar el bot. Crea un archivo `Procfile` en la raíz del proyecto:

```
worker: python bot.py
```

> Usa `worker` (no `web`) porque el bot no necesita un servidor HTTP.

### Paso 5 — Desplegar

Haz push a `main` y Railway desplegará automáticamente:

```bash
git add Procfile
git commit -m "Agrega Procfile para Railway"
git push origin main
```

Railway detecta los cambios, instala las dependencias de `requirements.txt` y arranca el bot. Puedes ver los logs en tiempo real desde el panel.

---

## Uso del bot

| Comando | Descripción |
|---|---|
| `/start` | Bienvenida |
| `/configurar` | Configura nombre, teléfono, email y moneda del negocio |
| `/logo` | Sube el logo (se guarda en Cloudinary) |
| `/nueva` | Inicia una nueva nota de venta |
| `/ayuda` | Muestra todos los comandos |
| `/cancelar` | Cancela la operación actual |

### Flujo de una nota de venta

```
/nueva
  → Nombre del cliente
  → N° documento / RUC
  → Dirección
  → Forma de pago  [botones]
  → Nombre del artículo
  → Cantidad
  → Precio unitario
  ↺  ¿Agregar otro artículo?  [botones]
  → Notas adicionales
  → Confirmar  [botones]
  ✅ PDF generado y enviado
```

---

## Estructura del proyecto

```
NotadeVenta/
├── bot.py               # Lógica principal del bot
├── pdf_generator.py     # Generación del PDF con ReportLab
├── config_manager.py    # Lectura/escritura de config.json
├── cloudinary_helper.py # Integración con Cloudinary
├── requirements.txt     # Dependencias Python
├── .env.example         # Plantilla de variables de entorno
├── .gitignore
├── Procfile             # (crear antes de desplegar en Railway)
└── data/
    └── config.json      # Creado automáticamente al configurar
```

---

## Variables de entorno

| Variable | Requerida | Descripción |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | Token del bot (BotFather) |
| `CLOUDINARY_CLOUD_NAME` | ✅* | Cloud name de Cloudinary |
| `CLOUDINARY_API_KEY` | ✅* | API key de Cloudinary |
| `CLOUDINARY_API_SECRET` | ✅* | API secret de Cloudinary |

*Requeridas solo si deseas usar el comando `/logo`. Sin ellas el bot funciona normalmente pero sin logo en el PDF.

---

## Notas técnicas

- La configuración del negocio y el contador de notas se guardan en `data/config.json`.
- En Railway, ese archivo **no persiste** entre reinicios. Para producción se recomienda reemplazar `ConfigManager` por una base de datos (Railway ofrece PostgreSQL gratuito).
- El logo se guarda en Cloudinary con la ruta `nota_venta/logo`, y se sobreescribe cada vez que usas `/logo`.
