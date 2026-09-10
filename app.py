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

# Données temporaires des utilisateurs
mises = {}
tokens = {}
paliers_atteints = {}
derniers_des = {}


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
        "💰 Mise mensuelle : /mise\n"
        "📊 Palier : /palier\n"
        "🎲 Lancer le dé : /de\n"
        "🧮 Calculatrice : /calcul\n"
        "🪙 Tokens : /token\n"
        "📈 Profil : /profil"
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
        "Réponds avec 1, 2, 3 ou 4."
    )


async def de(update: Update, context: ContextTypes.DEFAULT_TYPE):
    resultat = random.randint(1, 3)

    # Mémorise le dernier résultat pour cet utilisateur
    derniers_des[update.effective_user.id] = resultat

    await update.message.reply_text(
        "🎲 Lancement du dé...\n\n"
        f"🎯 Résultat : **{resultat}**",
        parse_mode="Markdown"
    )


async def calcul(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in derniers_des:
        await update.message.reply_text(
            "❌ Tu dois d'abord lancer le dé avec /de"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "🧮 Indique un nombre à multiplier.\n\n"
            "Exemple :\n"
            "/calcul 1.50"
        )
        return

    try:
        nombre = float(context.args[0].replace(",", "."))
        resultat_de = derniers_des[user_id]

        resultat = nombre * resultat_de

        await update.message.reply_text(
            f"🧮 {nombre:.2f} × {resultat_de} = "
            f"**{resultat:.2f} Token 🪙**",
            parse_mode="Markdown"
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Nombre invalide.\n\n"
            "Exemple : /calcul 1.50"
        )


async def token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🪙 Indique le nombre de tokens à ajouter ou retirer.\n\n"
            "Exemples :\n"
            "/token 3\n"
            "/token -1"
        )
        return

    try:
        variation = int(context.args[0])
        user_id = update.effective_user.id

        if user_id not in tokens:
            tokens[user_id] = 0

        if user_id not in paliers_atteints:
            paliers_atteints[user_id] = 1

        tokens[user_id] += variation

        # Minimum de 0 token
        if tokens[user_id] < 0:
            tokens[user_id] = 0

        # Vérification du meilleur palier atteint
        nouveau_palier = paliers_atteints[user_id]

        if tokens[user_id] >= 50:
            nouveau_palier = 5
        elif tokens[user_id] >= 30:
            nouveau_palier = max(nouveau_palier, 4)
        elif tokens[user_id] >= 20:
            nouveau_palier = max(nouveau_palier, 3)
        elif tokens[user_id] >= 10:
            nouveau_palier = max(nouveau_palier, 2)

        paliers_atteints[user_id] = nouveau_palier

        if nouveau_palier == 5:
            message_palier = "🏆 PALIER FINAL ×5 !"
        else:
            message_palier = f"📊 Palier actuel : ×{nouveau_palier}"

        await update.message.reply_text(
            f"🪙 Variation : {variation:+d} Token\n\n"
            f"💰 Total : {tokens[user_id]} Token\n"
            f"{message_palier}"
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Valeur invalide.\n\n"
            "Exemple : /token 3"
        )


async def profil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    total_tokens = tokens.get(user_id, 0)
    palier_actuel = paliers_atteints.get(user_id, 1)
    dernier_de = derniers_des.get(user_id, "—")

    if palier_actuel == 5:
        progression = "🏆 Palier final ×5"
    elif palier_actuel == 4:
        progression = "🔥 Palier ×4"
    elif palier_actuel == 3:
        progression = "🚀 Palier ×3"
    elif palier_actuel == 2:
        progression = "📈 Palier ×2"
    else:
        progression = "🔰 Départ"

    await update.message.reply_text(
        "📊 TON PROFIL TOKEN - LEVEL\n\n"
        f"🪙 Tokens : {total_tokens}\n"
        f"{progression}\n"
        f"🎲 Dernier dé : {dernier_de}\n\n"
        "🎯 BARÈME\n"
        "×2 → 10 tokens\n"
        "×3 → 20 tokens\n"
        "×4 → 30 tokens\n"
        "×5 → 50 tokens"
    )


async def recevoir_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texte = update.message.text.replace(",", ".").strip()

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
                "Exemple : 50"
            )

        return

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
                "Réponds avec 1, 2, 3 ou 4."
            )
            return

        mise_actuelle = mises.get(update.effective_user.id)

        if mise_actuelle is None:
            context.user_data["attente_palier"] = False

            await update.message.reply_text(
                "❌ Ta mise n'est plus enregistrée.\n\n"
                "Utilise /mise."
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


threading.Thread(target=start_web_server, daemon=True).start()

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mise", mise))
app.add_handler(CommandHandler("palier", palier))
app.add_handler(CommandHandler("de", de))
app.add_handler(CommandHandler("calcul", calcul))
app.add_handler(CommandHandler("token", token))
app.add_handler(CommandHandler("profil", profil))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        recevoir_message,
    )
)

app.run_polling()
