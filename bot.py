#!/usr/bin/env python3
"""Bot de Telegram para generar Notas de Venta en PDF."""

import logging
import os

from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from cloudinary_helper import CloudinaryHelper
from config_manager import ConfigManager
from pdf_generator import generate_pdf

load_dotenv()

logging.basicConfig(
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

config_manager   = ConfigManager()
cloudinary_helper = CloudinaryHelper()

# ── Estados de las conversaciones ─────────────────────────────────────────────

# /configurar
CFG_NOMBRE, CFG_TELEFONO, CFG_EMAIL, CFG_MONEDA = range(4)

# /logo
(LOGO_UPLOAD,) = range(4, 5)

# /nueva
(
    NV_CLIENTE_NOMBRE,
    NV_CLIENTE_RUC,
    NV_CLIENTE_DIRECCION,
    NV_CLIENTE_PAGO,
    NV_ARTICULO_NOMBRE,
    NV_ARTICULO_CANTIDAD,
    NV_ARTICULO_PRECIO,
    NV_ARTICULO_MAS,
    NV_NOTAS,
    NV_CONFIRMAR,
) = range(5, 15)

# ── Opciones de pago ───────────────────────────────────────────────────────────
FORMAS_PAGO = ["Efectivo", "Transferencia", "Tarjeta", "Cheque", "Crédito", "Otro"]


# ─────────────────────────────────────────────────────────────────────────────
# Teclados inline
# ─────────────────────────────────────────────────────────────────────────────

def _kb_pago() -> InlineKeyboardMarkup:
    buttons, row = [], []
    for i, opcion in enumerate(FORMAS_PAGO):
        row.append(InlineKeyboardButton(opcion, callback_data=f"pago|{opcion}"))
        if (i + 1) % 3 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def _kb_articulo_mas() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("➕ Agregar otro artículo", callback_data="art|si"),
        InlineKeyboardButton("🏁 Terminar artículos",   callback_data="art|no"),
    ]])


def _kb_confirmar() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📄 Generar PDF",  callback_data="conf|si"),
        InlineKeyboardButton("❌ Cancelar",     callback_data="conf|no"),
    ]])


# ─────────────────────────────────────────────────────────────────────────────
# /start  y  /ayuda
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "👋 *¡Bienvenido al Bot de Notas de Venta!*\n\n"
        "Este bot genera notas de venta profesionales en PDF directamente en Telegram.\n\n"
        "Usa /ayuda para ver todos los comandos disponibles.",
        parse_mode="Markdown",
    )


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 *Comandos disponibles*\n\n"
        "⚙️  /configurar — Configura los datos de tu negocio\n"
        "🖼️  /logo — Sube el logo de tu negocio\n"
        "📝  /nueva — Crea una nueva nota de venta\n"
        "❓  /ayuda — Muestra esta ayuda\n"
        "🚫  /cancelar — Cancela la operación actual\n\n"
        "_Empieza con /configurar si es tu primera vez._",
        parse_mode="Markdown",
    )


# ─────────────────────────────────────────────────────────────────────────────
# /cancelar  (funciona dentro de cualquier conversación)
# ─────────────────────────────────────────────────────────────────────────────

async def cmd_cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "🚫 Operación cancelada.\n\nUsa /ayuda para ver los comandos disponibles."
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# /configurar
# ─────────────────────────────────────────────────────────────────────────────

async def cfg_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    existing = config_manager.get_config()
    if existing:
        await update.message.reply_text(
            "⚙️ *Actualizar configuración*\n\n"
            f"• Negocio: *{existing.get('nombre', '-')}*\n"
            f"• Teléfono: {existing.get('telefono', '-')}\n"
            f"• Email: {existing.get('email', '-')}\n"
            f"• Moneda: {existing.get('moneda', '-')}\n\n"
            "Ingresa los nuevos valores _(o los mismos si no deseas cambiarlos)_.\n\n"
            "✏️ *Nombre del negocio:*",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "⚙️ *Configuración inicial del negocio*\n\n"
            "Vamos a guardar los datos de tu negocio para las notas de venta.\n\n"
            "✏️ *Nombre del negocio:*",
            parse_mode="Markdown",
        )
    return CFG_NOMBRE


async def cfg_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cfg"] = {"nombre": update.message.text.strip()}
    await update.message.reply_text("📞 *Teléfono:*", parse_mode="Markdown")
    return CFG_TELEFONO


async def cfg_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cfg"]["telefono"] = update.message.text.strip()
    await update.message.reply_text("📧 *Email:*", parse_mode="Markdown")
    return CFG_EMAIL


async def cfg_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cfg"]["email"] = update.message.text.strip()
    await update.message.reply_text(
        "💰 *Moneda* _(ej: PEN, USD, MXN, ARS, CLP, EUR):_",
        parse_mode="Markdown",
    )
    return CFG_MONEDA


async def cfg_moneda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["cfg"]["moneda"] = update.message.text.strip().upper()

    # Conserva datos previos (logo_url, ultimo_numero, etc.)
    existing = config_manager.get_config() or {}
    existing.update(context.user_data["cfg"])
    config_manager.save_config(existing)

    cfg = existing
    await update.message.reply_text(
        "✅ *¡Configuración guardada correctamente!*\n\n"
        f"• Negocio: *{cfg['nombre']}*\n"
        f"• Teléfono: {cfg['telefono']}\n"
        f"• Email: {cfg['email']}\n"
        f"• Moneda: {cfg['moneda']}\n\n"
        "Ahora puedes usar:\n"
        "🖼️ /logo — para subir tu logo\n"
        "📝 /nueva — para crear una nota de venta",
        parse_mode="Markdown",
    )
    context.user_data.clear()
    return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# /logo
# ─────────────────────────────────────────────────────────────────────────────

async def logo_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not config_manager.is_configured():
        await update.message.reply_text(
            "⚠️ Primero debes configurar tu negocio con /configurar"
        )
        return ConversationHandler.END

    if not cloudinary_helper.is_configured():
        await update.message.reply_text(
            "⚠️ Las credenciales de Cloudinary no están configuradas en el archivo *.env*.\n\n"
            "Agrega las variables:\n"
            "`CLOUDINARY_CLOUD_NAME`\n"
            "`CLOUDINARY_API_KEY`\n"
            "`CLOUDINARY_API_SECRET`\n\n"
            "Consulta el README para más información.",
            parse_mode="Markdown",
        )
        return ConversationHandler.END

    config = config_manager.get_config()
    if config.get("logo_url"):
        await update.message.reply_text(
            "🖼️ Ya tienes un logo cargado. Envía la nueva imagen para reemplazarlo.\n"
            "_(JPG o PNG — recomendado: cuadrado, al menos 200×200 px)_",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "🖼️ *Subir logo del negocio*\n\n"
            "Envía la imagen del logo.\n"
            "_(JPG o PNG — recomendado: cuadrado, al menos 200×200 px)_",
            parse_mode="Markdown",
        )
    return LOGO_UPLOAD


async def logo_upload(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    msg = await update.message.reply_text("⏳ Subiendo logo a Cloudinary...")

    try:
        if update.message.photo:
            tg_file = await update.message.photo[-1].get_file()
        else:
            tg_file = await update.message.document.get_file()

        file_bytes = bytes(await tg_file.download_as_bytearray())
        url        = cloudinary_helper.upload_logo(file_bytes)
        config_manager.update_logo(url)

        await msg.edit_text(
            "✅ *¡Logo subido correctamente!*\n\n"
            "Tu logo aparecerá en todas las notas de venta.\n\n"
            "Usa /nueva para crear una nota.",
            parse_mode="Markdown",
        )
    except Exception as exc:
        logger.exception("Error subiendo logo")
        await msg.edit_text(
            f"❌ Error al subir el logo:\n`{exc}`\n\nIntenta de nuevo con /logo",
            parse_mode="Markdown",
        )

    return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# /nueva  — flujo completo paso a paso
# ─────────────────────────────────────────────────────────────────────────────

async def nueva_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not config_manager.is_configured():
        await update.message.reply_text(
            "⚠️ Primero debes configurar tu negocio con /configurar"
        )
        return ConversationHandler.END

    context.user_data["venta"] = {
        "cliente":   {},
        "articulos": [],
        "notas":     "",
    }
    context.user_data["art_actual"] = {}

    await update.message.reply_text(
        "📝 *Nueva Nota de Venta*\n\n"
        "Ingresaremos los datos del cliente y los artículos paso a paso.\n"
        "_(Escribe /cancelar en cualquier momento para salir)_\n\n"
        "👤 *Nombre del cliente / Razón social:*",
        parse_mode="Markdown",
    )
    return NV_CLIENTE_NOMBRE


# ── Datos del cliente ──────────────────────────────────────────────────────────

async def nv_cliente_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["venta"]["cliente"]["nombre"] = update.message.text.strip()
    await update.message.reply_text(
        "🔢 *N° de documento / RUC:*\n_(Escribe `-` si no aplica)_",
        parse_mode="Markdown",
    )
    return NV_CLIENTE_RUC


async def nv_cliente_ruc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["venta"]["cliente"]["ruc"] = update.message.text.strip()
    await update.message.reply_text(
        "📍 *Dirección:*\n_(Escribe `-` si no aplica)_",
        parse_mode="Markdown",
    )
    return NV_CLIENTE_DIRECCION


async def nv_cliente_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["venta"]["cliente"]["direccion"] = update.message.text.strip()
    await update.message.reply_text(
        "💳 *Forma de pago:*",
        parse_mode="Markdown",
        reply_markup=_kb_pago(),
    )
    return NV_CLIENTE_PAGO


async def nv_cliente_pago_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pago = query.data.split("|", 1)[1]
    context.user_data["venta"]["cliente"]["pago"] = pago

    await query.edit_message_text(
        f"💳 Forma de pago: *{pago}* ✓\n\n"
        "──────────────────────\n"
        "🛒 *Artículos*\n\n"
        "📦 *Nombre del primer artículo:*",
        parse_mode="Markdown",
    )
    return NV_ARTICULO_NOMBRE


# ── Artículos ──────────────────────────────────────────────────────────────────

async def nv_art_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["art_actual"] = {"nombre": update.message.text.strip()}
    await update.message.reply_text(
        "🔢 *Cantidad:*",
        parse_mode="Markdown",
    )
    return NV_ARTICULO_CANTIDAD


async def nv_art_cantidad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        qty = float(update.message.text.strip().replace(",", "."))
        if qty <= 0:
            raise ValueError
        context.user_data["art_actual"]["cantidad"] = qty
        await update.message.reply_text("💵 *Precio unitario:*", parse_mode="Markdown")
        return NV_ARTICULO_PRECIO
    except ValueError:
        await update.message.reply_text("⚠️ Ingresa una cantidad válida mayor a 0.")
        return NV_ARTICULO_CANTIDAD


async def nv_art_precio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        precio = float(update.message.text.strip().replace(",", "."))
        if precio < 0:
            raise ValueError

        art = context.user_data["art_actual"]
        art["precio"]   = precio
        art["subtotal"] = round(art["cantidad"] * precio, 2)

        context.user_data["venta"]["articulos"].append(dict(art))
        context.user_data["art_actual"] = {}

        config  = config_manager.get_config()
        moneda  = config.get("moneda", "USD")
        n       = len(context.user_data["venta"]["articulos"])
        qty_str = (
            str(int(art["cantidad"])) if art["cantidad"] == int(art["cantidad"])
            else f"{art['cantidad']:.2f}"
        )

        await update.message.reply_text(
            f"✅ *Artículo #{n} agregado:*\n"
            f"`{art['nombre']}`\n"
            f"  {qty_str} × {moneda} {art['precio']:.2f} = *{moneda} {art['subtotal']:.2f}*\n\n"
            "¿Deseas agregar otro artículo?",
            parse_mode="Markdown",
            reply_markup=_kb_articulo_mas(),
        )
        return NV_ARTICULO_MAS

    except ValueError:
        await update.message.reply_text("⚠️ Ingresa un precio válido (número ≥ 0).")
        return NV_ARTICULO_PRECIO


async def nv_art_mas_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "art|si":
        await query.edit_message_text(
            "📦 *Nombre del siguiente artículo:*",
            parse_mode="Markdown",
        )
        return NV_ARTICULO_NOMBRE

    await query.edit_message_text(
        "📝 *Notas adicionales:*\n"
        "_(Condiciones, observaciones, garantía… o escribe `-` para omitir)_",
        parse_mode="Markdown",
    )
    return NV_NOTAS


# ── Notas y confirmación ───────────────────────────────────────────────────────

async def nv_notas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    texto = update.message.text.strip()
    context.user_data["venta"]["notas"] = "" if texto == "-" else texto

    venta  = context.user_data["venta"]
    config = config_manager.get_config()
    moneda = config.get("moneda", "USD")
    total  = sum(a["subtotal"] for a in venta["articulos"])

    lineas = "\n".join(
        f"  {i+1}. {a['nombre']} — "
        f"{int(a['cantidad']) if a['cantidad'] == int(a['cantidad']) else a['cantidad']:.2f}"
        f" × {moneda} {a['precio']:.2f} = *{moneda} {a['subtotal']:.2f}*"
        for i, a in enumerate(venta["articulos"])
    )

    resumen = (
        "📋 *Resumen de la nota de venta*\n\n"
        f"👤 Cliente: {venta['cliente']['nombre']}\n"
        f"🔢 Doc/RUC: {venta['cliente']['ruc']}\n"
        f"📍 Dirección: {venta['cliente']['direccion']}\n"
        f"💳 Pago: {venta['cliente']['pago']}\n\n"
        f"🛒 *Artículos:*\n{lineas}\n\n"
        f"💰 *TOTAL: {moneda} {total:.2f}*"
    )
    if venta["notas"]:
        resumen += f"\n\n📝 Notas: {venta['notas']}"

    resumen += "\n\n¿Generamos el PDF?"

    await update.message.reply_text(
        resumen,
        parse_mode="Markdown",
        reply_markup=_kb_confirmar(),
    )
    return NV_CONFIRMAR


async def nv_confirmar_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "conf|no":
        await query.edit_message_text("🚫 Nota de venta cancelada.")
        context.user_data.clear()
        return ConversationHandler.END

    await query.edit_message_text("⏳ Generando PDF, por favor espera…")

    try:
        config  = config_manager.get_config()
        venta   = context.user_data["venta"]
        numero  = config_manager.get_next_sale_number()
        venta["numero"] = numero

        pdf_bytes = generate_pdf(venta, config)
        moneda    = config.get("moneda", "USD")
        total     = sum(a["subtotal"] for a in venta["articulos"])
        filename  = f"nota_venta_{numero:04d}.pdf"

        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=pdf_bytes,
            filename=filename,
            caption=(
                f"📄 *Nota de Venta #{numero:04d}*\n"
                f"Cliente: {venta['cliente']['nombre']}\n"
                f"Total: {moneda} {total:.2f}"
            ),
            parse_mode="Markdown",
        )

    except Exception as exc:
        logger.exception("Error generando PDF")
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Error al generar el PDF:\n`{exc}`",
            parse_mode="Markdown",
        )

    context.user_data.clear()
    return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# Armado de la aplicación
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("Variable TELEGRAM_BOT_TOKEN no encontrada en el archivo .env")

    app = Application.builder().token(token).build()

    # ── /configurar ──────────────────────────────────────────────────────────
    cfg_conv = ConversationHandler(
        entry_points=[CommandHandler("configurar", cfg_start)],
        states={
            CFG_NOMBRE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, cfg_nombre)],
            CFG_TELEFONO: [MessageHandler(filters.TEXT & ~filters.COMMAND, cfg_telefono)],
            CFG_EMAIL:    [MessageHandler(filters.TEXT & ~filters.COMMAND, cfg_email)],
            CFG_MONEDA:   [MessageHandler(filters.TEXT & ~filters.COMMAND, cfg_moneda)],
        },
        fallbacks=[CommandHandler("cancelar", cmd_cancelar)],
        allow_reentry=True,
    )

    # ── /logo ─────────────────────────────────────────────────────────────────
    logo_conv = ConversationHandler(
        entry_points=[CommandHandler("logo", logo_start)],
        states={
            LOGO_UPLOAD: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, logo_upload)
            ],
        },
        fallbacks=[CommandHandler("cancelar", cmd_cancelar)],
        allow_reentry=True,
    )

    # ── /nueva ────────────────────────────────────────────────────────────────
    nueva_conv = ConversationHandler(
        entry_points=[CommandHandler("nueva", nueva_start)],
        states={
            NV_CLIENTE_NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_cliente_nombre)],
            NV_CLIENTE_RUC:       [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_cliente_ruc)],
            NV_CLIENTE_DIRECCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_cliente_direccion)],
            NV_CLIENTE_PAGO:      [CallbackQueryHandler(nv_cliente_pago_cb, pattern=r"^pago\|")],
            NV_ARTICULO_NOMBRE:   [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_art_nombre)],
            NV_ARTICULO_CANTIDAD: [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_art_cantidad)],
            NV_ARTICULO_PRECIO:   [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_art_precio)],
            NV_ARTICULO_MAS:      [CallbackQueryHandler(nv_art_mas_cb, pattern=r"^art\|")],
            NV_NOTAS:             [MessageHandler(filters.TEXT & ~filters.COMMAND, nv_notas)],
            NV_CONFIRMAR:         [CallbackQueryHandler(nv_confirmar_cb, pattern=r"^conf\|")],
        },
        fallbacks=[CommandHandler("cancelar", cmd_cancelar)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("ayuda",   cmd_ayuda))
    app.add_handler(cfg_conv)
    app.add_handler(logo_conv)
    app.add_handler(nueva_conv)

    logger.info("Bot iniciado. Esperando mensajes…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
