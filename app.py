import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

# Stockage temporaire des mises
mises = {}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Token - Level Bot is running!")

    def log_message(self, format, *args):
        pass


def start_web_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Bienvenue sur Token - Level !\n\n"
        "Le bot est bien connecté.\n\n"
        "💰 Pour définir ta mise mensuelle, utilise :\n"
        "/mise"
    )


async def mise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["attente_mise"] = True

    await update.message.reply_text(
        "💰 Quelle est ta mise mensuelle de départ ?\n\n"
        "Exemple : 50"
    )


async def recevoir_mise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("attente_mise"):
        return

    texte = update.message.text.replace(",", ".").strip()

    try:
        montant = float(texte)

        if montant <= 0:
            raise ValueError

        mises[update.effective_user.id] = montant
        context.user_data["attente_mise"] = False

        await update.message.reply_text(
            f"✅ Mise mensuelle enregistrée : {montant:.2f} €\n\n"
            "Ton profil Token - Level est prêt pour la suite. 🚀"
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Montant invalide.\n\n"
            "Envoie simplement un montant, par exemple : 50"
        )


threading.Thread(target=start_web_server, daemon=True).start()

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mise", mise))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, recevoir_mise))

app.run_polling()
