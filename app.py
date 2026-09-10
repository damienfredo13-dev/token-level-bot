import os
import threading
import random
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

# Stockage temporaire des données utilisateurs
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
        "💰 Définir ta mise mensuelle : /mise\n"
        "📊 Enregistrer ton palier : /palier\n"
        "🎲 Lancer le dé : /de"
    )


async def mise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["attente_mise"] = True
    context.user_data["attente_palier"] = False

    await update.message.reply_text(
        "💰 Quelle est ta mise mensuelle de départ ?\n\n"
        "Exemple : 50"
    )


async def palier(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mise_actuelle = mises.get(update.effective_user.id)

    if mise_actuelle is None:
        await update.message.reply_text(
            "❌ Tu dois d'abord définir ta mise avec /mise"
        )
        return

    context.user_data["attente_palier"] = True
    context.user_data["attente_mise"] = False

    await update.message.reply_text(
        "📊 Quel palier as-tu atteint ?\n\n"
        "1️⃣ ×2\n"
        "2️⃣ ×3\n"
        "3️⃣ ×4\n"
        "4️⃣ ×5\n\n"
        "Réponds simplement avec 1, 2, 3 ou 4."
    )


async def de(update: Update, context: ContextTypes.DEFAULT_TYPE):
    multiplicateur = random.randint(1, 3)

    await update.message.reply_text(
        "🎲 Lancement du dé...\n\n"
        f"🎯 Résultat : **{multiplicateur}**",
        parse_mode="Markdown"
    )


async def recevoir_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte = update.message.text.replace(",", ".").strip()

    # Enregistrement de la mise
    if context.user_data.get("attente_mise"):

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

        return

    # Enregistrement du palier
    if context.user_data.get("attente_palier"):

        paliers = {
            "1": 2,
            "2": 3,
            "3": 4,
            "4": 5,
        }

        if texte not in paliers:
            await update.message.reply_text(
                "❌ Choix invalide.\n\n"
                "Réponds avec : 1, 2, 3 ou 4."
            )
            return

        mise_actuelle = mises.get(update.effective_user.id)

        if mise_actuelle is None:
            context.user_data["attente_palier"] = False

            await update.message.reply_text(
                "❌ Ta mise n'est plus enregistrée.\n\n"
                "Utilise /mise pour la définir à nouveau."
            )
            return

        multiplicateur = paliers[texte]
        montant_atteint = mise_actuelle * multiplicateur
        benefice = montant_atteint - mise_actuelle

        context.user_data["attente_palier"] = False

        await update.message.reply_text(
            f"🎯 Palier enregistré : ×{multiplicateur}\n\n"
            f"💰 Mise de départ : {mise_actuelle:.2f} €\n"
            f"📈 Montant atteint : {montant_atteint:.2f} €\n"
            f"💵 Bénéfice : +{benefice:.2f} €\n\n"
            f"🔄 Base du mois suivant : {mise_actuelle:.2f} €"
        )

        return


threading.Thread(target=start_web_server, daemon=True).start()

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mise", mise))
app.add_handler(CommandHandler("palier", palier))
app.add_handler(CommandHandler("de", de))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        recevoir_message,
    )
)

app.run_polling()
