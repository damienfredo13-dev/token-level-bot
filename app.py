import os
import threading
import random
import html
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

# ID du canal Token - Level
CHANNEL_ID = -1004324987579

# ID du propriétaire du canal
OWNER_ID = None

# Données temporaires des utilisateurs
mises = {}
tokens = {}
paliers_atteints = {}
derniers_des = {}

# Série de victoires consécutives
victoires_consecutives = {}

# Boost actuellement chargé pour le prochain gain
boost_actif = {}

# Permet de savoir quels boosts ont déjà été débloqués pendant la série
boosts_debloques = {}


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


# ============================================================
# ENVOI DANS LE CANAL
# ============================================================

async def envoyer_au_canal(context, texte):
    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=texte,
        parse_mode="Markdown"
    )


# ============================================================
# START
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["attente_mise"] = False
    context.user_data["attente_palier"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    await update.message.reply_text(
        "🚀 Bienvenue sur Token - Level !\n\n"
        "Le bot est bien connecté.\n\n"
        "💰 Mise mensuelle : /mise\n"
        "📊 Palier : /palier\n"
        "🚨 Rappel palier : /rappel\n"
        "🎲 Lancer le dé : /de\n"
        "🧮 Calculatrice : /calcul\n"
        "🪙 Tokens : /token\n"
        "📈 Profil : /profil\n"
        "🎉 Victoire : /gagne\n"
        "💔 Défaite : /perdu\n"
        "🔥 Boost : /boost\n"
        "⚽ Goal : /goal\n"
        "🟥 VAR : /var\n"
        "✍️ Message personnalisé : /message\n"
        "🎯 Bet : /bet\n"
        "🔄 Reset : /reset"
    )


# ============================================================
# MISE
# ============================================================

async def mise(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["attente_mise"] = True
    context.user_data["attente_palier"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    await update.message.reply_text(
        "💰 Quelle est ta mise mensuelle de départ ?\n\n"
        "Exemple : 50"
    )


# ============================================================
# PALIER
# ============================================================

async def palier(update: Update, context: ContextTypes.DEFAULT_TYPE):

    mise_actuelle = mises.get(update.effective_user.id)

    if mise_actuelle is None:
        await update.message.reply_text(
            "❌ Tu dois d'abord définir ta mise avec /mise"
        )
        return

    context.user_data["attente_palier"] = True
    context.user_data["attente_mise"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    await update.message.reply_text(
        "📊 Quel palier as-tu atteint ?\n\n"
        "1️⃣ ×2\n"
        "2️⃣ ×3\n"
        "3️⃣ ×4\n"
        "4️⃣ ×5\n\n"
        "Réponds avec 1, 2, 3 ou 4."
    )


# ============================================================
# RAPPEL PALIER
# ============================================================

async def rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    mise_actuelle = mises.get(user_id)

    if mise_actuelle is None:
        await update.message.reply_text(
            "❌ Tu dois d'abord définir ta mise avec /mise"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "🚨 RAPPEL PALIER 🚨\n\n"
            "Indique le palier à rappeler.\n\n"
            "Exemples :\n"
            "/rappel 2\n"
            "/rappel 3\n"
            "/rappel 4\n"
            "/rappel 5"
        )
        return

    try:
        palier_rappel = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Palier invalide.\n\n"
            "Utilise uniquement : 2, 3, 4 ou 5."
        )
        return

    if palier_rappel < 2 or palier_rappel > 5:
        await update.message.reply_text(
            "❌ Palier invalide.\n\n"
            "Utilise uniquement : 2, 3, 4 ou 5."
        )
        return

    context.user_data["attente_mise"] = False
    context.user_data["attente_palier"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    if palier_rappel < 5:

        message = (
            "🚨 **RAPPEL** 🚨\n\n"
            f"🎯 **PALIER ×{palier_rappel} ATTEINT !**\n\n"
            f"💰 Mise de départ : **{mise_actuelle:.2f} €**\n"
            f"📈 **FOIS {palier_rappel} ACQUIS ✅**\n"
            f"💵 **MERCI LE PALIER {palier_rappel} !!**\n\n"
            f"🚗 En route pour le palier {palier_rappel + 1} !!!"
        )

    else:

        message = (
            "🚨 **RAPPEL** 🚨\n\n"
            "🎯 **PALIER ×5 ATTEINT !**\n\n"
            f"💰 Mise de départ : **{mise_actuelle:.2f} €**\n"
            "📈 **FOIS 5 ACQUIS ✅**\n"
            "💵 **MERCI LE PALIER 5 !!**\n\n"
            "🏆 **OBJECTIF FINAL ATTEINT !!!**"
        )

    await envoyer_au_canal(context, message)

    await update.message.reply_text(
        f"✅ Rappel du palier {palier_rappel} publié dans le canal !"
    )


# ============================================================
# DE
# ============================================================

async def de(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["attente_mise"] = False
    context.user_data["attente_palier"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    resultat = random.randint(1, 3)

    derniers_des[update.effective_user.id] = resultat

    message = (
        "🎲 **LANCEMENT DU DÉ** 🎲\n\n"
        f"🎯 Résultat : **{resultat}**"
    )

    await envoyer_au_canal(context, message)

    await update.message.reply_text(
        "✅ Résultat du dé publié dans le canal !"
    )


# ============================================================
# CALCUL
# ============================================================

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

        message = (
            "🧮 **CALCUL TOKEN - LEVEL**\n\n"
            f"💰 Base : **{nombre:.2f}**\n"
            f"🎲 Dé : **{resultat_de}**\n\n"
            f"🪙 Résultat : **{resultat:.2f} Token**"
        )

        await envoyer_au_canal(context, message)

        await update.message.reply_text(
            "✅ Calcul publié dans le canal !"
        )

    except ValueError:
        await update.message.reply_text(
            "❌ Nombre invalide.\n\n"
            "Exemple : /calcul 1.50"
        )


# ============================================================
# TOKEN
# ============================================================

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

        variation_originale = variation
        boost_utilise = None

        if variation > 0 and user_id in boost_actif:

            multiplicateur = boost_actif[user_id]
            variation = variation * multiplicateur
            boost_utilise = multiplicateur

            del boost_actif[user_id]

        tokens[user_id] += variation

        if tokens[user_id] < 0:
            tokens[user_id] = 0

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

        if boost_utilise:

            message = (
                "🚀 **SUPER BOOST UTILISÉ !** 🚀\n\n"
                f"🔥 Boost : **×{boost_utilise}**\n"
                f"🪙 Gain initial : **+{variation_originale} Token**\n"
                f"💥 Gain boosté : **+{variation} Token**\n\n"
                f"💰 Total : **{tokens[user_id]} Token**\n"
                f"{message_palier}"
            )

        else:

            message = (
                "🪙 **TOKEN - LEVEL**\n\n"
                f"📈 Variation : **{variation:+d} Token**\n\n"
                f"💰 Total : **{tokens[user_id]} Token**\n"
                f"{message_palier}"
            )

        await envoyer_au_canal(context, message)

        if boost_utilise:
            await update.message.reply_text(
                f"🚀 BOOST ×{boost_utilise} utilisé !\n"
                f"🪙 Ton gain de +{variation_originale} Token devient "
                f"+{variation} Token !"
            )
        else:
            await update.message.reply_text(
                "✅ Mise à jour des Tokens publiée dans le canal !"
            )

    except ValueError:
        await update.message.reply_text(
            "❌ Valeur invalide.\n\n"
            "Exemple : /token 3"
        )


# ============================================================
# PROFIL
# ============================================================

async def profil(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    total_tokens = tokens.get(user_id, 0)
    palier_actuel = paliers_atteints.get(user_id, 1)
    dernier_de = derniers_des.get(user_id, "—")
    serie = victoires_consecutives.get(user_id, 0)
    boost = boost_actif.get(user_id)

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

    if boost:
        boost_message = f"🚀 Boost actif : ×{boost}"
    else:
        boost_message = "🚀 Boost actif : aucun"

    message = (
        "📊 **TON PROFIL TOKEN - LEVEL**\n\n"
        f"🪙 Tokens : **{total_tokens}**\n"
        f"{progression}\n"
        f"🎲 Dernier dé : **{dernier_de}**\n"
        f"🔥 Série : **{serie} victoire(s)**\n"
        f"{boost_message}\n\n"
        "🎯 **BARÈME**\n"
        "×2 → 10 tokens\n"
        "×3 → 20 tokens\n"
        "×4 → 30 tokens\n"
        "×5 → 50 tokens"
    )

    await envoyer_au_canal(context, message)

    await update.message.reply_text(
        "✅ Profil publié dans le canal !"
    )


# ============================================================
# GAGNE
# ============================================================

async def gagne(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    victoires_consecutives[user_id] = (
        victoires_consecutives.get(user_id, 0) + 1
    )

    serie = victoires_consecutives[user_id]

    if user_id not in boosts_debloques:
        boosts_debloques[user_id] = set()

    message = (
        "🚨💥 **ENCORE UNE VICTOIRE !** 💥🚨\n\n"
        "🎯 **PARI GAGNÉ !**\n"
        "🪙 Des **Tokens supplémentaires** viennent de tomber !\n\n"
        f"🔥 **SÉRIE EN COURS : {serie} VICTOIRE(S) D’AFFILÉE !** 🔥\n\n"
        "📈 Le compteur grimpe encore...\n"
        "🏆 Les paliers se rapprochent...\n\n"
        "👀 **Mais où va-t-il s'arrêter ?!**\n\n"
        "⚡️ Une chose est sûre :\n"
        "**il n’a clairement pas fini de ramasser des Tokens.** 🪙💰"
    )

    await envoyer_au_canal(context, message)

    if serie in [3, 5, 10] and serie not in boosts_debloques[user_id]:

        boosts_debloques[user_id].add(serie)

        if serie == 3:
            boost_message = (
                "🔥 **3 VICTOIRES D’AFFILÉE !!!** 🔥\n\n"
                "🚨 **SUPER BOOST ACTIVÉ !** 🚨\n\n"
                "🪙 **PROCHAIN GAIN DE TOKENS = ×2 !** 💥\n\n"
                "🎯 Le boost est chargé…\n"
                "👀 **À toi de choisir le bon moment !**\n\n"
                "🚀 **ON VA CHERCHER LE DOUBLE !**"
            )

        elif serie == 5:
            boost_message = (
                "🔥🔥 **5 VICTOIRES D’AFFILÉE !!!** 🔥🔥\n\n"
                "🚨 **SUPER BOOST ×3 ACTIVÉ !** 🚨\n\n"
                "🪙 **PROCHAIN GAIN DE TOKENS = ×3 !!!** 💥💥💥\n\n"
                "🔥 La série est en feu.\n"
                "👀 **ÇA COMMENCE À DEVENIR TRÈS SÉRIEUX…**\n\n"
                "🚀 **ON VA CHERCHER LE TRIPLE !**"
            )

        else:
            boost_message = (
                "🚨🚨🚨 **10 VICTOIRES D’AFFILÉE !!!** 🚨🚨🚨\n\n"
                "🏆🔥 **SÉRIE LÉGENDAIRE !** 🔥🏆\n\n"
                "🚀🚀 **BOOST FUSÉE ACTIVÉ !!!** 🚀🚀\n\n"
                "🪙 **PROCHAIN GAIN DE TOKENS = ×10 !!!** 💥💥💥\n\n"
                "💣💣💣 **×10 TOKENS !** 💣💣💣\n\n"
                "👑 **10 PARIS. 10 VICTOIRES.**\n\n"
                "🚀 **ON DÉCOLLE POUR LE ×10 !!!**\n\n"
                "🪙🔥 **TOKEN - LEVEL EST EN FUSION !**"
            )

        await envoyer_au_canal(context, boost_message)

    await update.message.reply_text(
        f"✅ Victoire publiée !\n"
        f"🔥 Série actuelle : {serie} victoire(s) d’affilée."
    )


# ============================================================
# PERDU
# ============================================================

async def perdu(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    victoires_consecutives[user_id] = 0

    boost_actif.pop(user_id, None)
    boosts_debloques[user_id] = set()

    message = (
        "💀😂 **ET BAH ALORS… ON A GLISSÉ CHEF !** 😂💀\n\n"
        "🎯 Cette fois, le pari nous a dit : **« NON. »** 😭\n\n"
        "🪙 Un Token s’est fait la malle…\n"
        "🏃‍♂️💨 Mais pas de panique, il reviendra avec ses copains !\n\n"
        "🤣 On perd une bataille, **pas la guerre !**\n"
        "🔥 On relève la tête !\n"
        "📈 On repart chercher les prochains Tokens !\n\n"
        "🍀 **La prochaine, c’est peut-être le jackpot…**\n"
        "👀 Alors on garde le sourire et on continue !\n\n"
        "🪙💪 **TOKEN - LEVEL : ON LÂCHE RIEN !** 🚀"
    )

    await envoyer_au_canal(context, message)

    await update.message.reply_text(
        "💔 Défaite publiée dans le canal !\n"
        "🔄 Série remise à 0."
    )


# ============================================================
# BOOST
# ============================================================

async def boost(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    serie = victoires_consecutives.get(user_id, 0)

    context.user_data["attente_boost"] = False

    if serie < 3:

        await update.message.reply_text(
            "🔒 **BOOST VERROUILLÉ** 🔒\n\n"
            f"🔥 Série actuelle : **{serie} victoire(s)**\n\n"
            "Il faut au minimum **3 victoires d’affilée**.\n\n"
            "🎯 3 victoires → BOOST ×2\n"
            "🎯 5 victoires → BOOST ×3\n"
            "🎯 10 victoires → BOOST FUSÉE ×10"
        )
        return

    disponibles = []

    if serie >= 3:
        disponibles.append("2️⃣ BOOST ×2")

    if serie >= 5:
        disponibles.append("3️⃣ BOOST ×3")

    if serie >= 10:
        disponibles.append("🔟 BOOST FUSÉE ×10")

    context.user_data["attente_boost"] = True

    await update.message.reply_text(
        "🚀 **SUPER BOOST** 🚀\n\n"
        f"🔥 Série actuelle : **{serie} victoire(s) d’affilée**\n\n"
        "Choisis ton boost :\n\n"
        + "\n".join(disponibles)
        + "\n\n"
        "Réponds avec **2**, **3** ou **10**."
    )


# ============================================================
# GOAL
# ============================================================

async def goal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "🚨⚽ **GOOOOOOOOOOOOOOOOOOOOOOOOAAAAAALLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL !!!!!!** ⚽🚨\n\n"
        "🔥🔥 **IL EST LÀÀÀÀÀÀÀÀÀÀÀÀÀÀÀ !!!** 🔥🔥\n\n"
        "💰 **GOAL VALIDÉ !**\n"
        "🚀 **ON MONTE D’UN NIVEAU !**"
    )

    await envoyer_au_canal(context, message)

    await update.message.reply_text(
        "✅ GOAL publié dans le canal !"
    )


# ============================================================
# VAR
# ============================================================

async def var(update: Update, context: ContextTypes.DEFAULT_TYPE):

    message = (
        "🚨🟥 **ARRÊTEZ TOUT !!!**\n\n"
        "🧑‍⚖️ **L’ARBITRE NOUS A ENCULÉS !!!** 😭🤬\n\n"
        "📺 **LE VAR EST EN TRAIN DE CHERCHER UNE EXCUSE...** 🤡\n\n"
        "❌ **BUT REFUSÉ !!!**\n\n"
        "💀 **ON S’EST FAIT VOLER !!!**"
    )

    await envoyer_au_canal(context, message)

    await update.message.reply_text(
        "🟥 VAR publié dans le canal !"
    )


# ============================================================
# MESSAGE PERSONNALISÉ
# ============================================================

async def message_personnalise(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["attente_mise"] = False
    context.user_data["attente_palier"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    context.user_data["attente_message"] = True

    await update.message.reply_text(
        "✍️ **MESSAGE À PUBLIER**\n\n"
        "Envoie-moi maintenant le message que tu veux publier dans le canal."
    )


# ============================================================
# BET
# ============================================================

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):

    context.user_data["attente_mise"] = False
    context.user_data["attente_palier"] = False
    context.user_data["confirmation_reset"] = False
    context.user_data["proposition_owner"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    context.user_data["attente_bet"] = True

    await update.message.reply_text(
        "🎯 **SUR QUOI TU MISES ?**\n\n"
        "Écris simplement ton pari.\n\n"
        "Exemple : **Olise buteur**"
    )


# ============================================================
# RESET
# ============================================================

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    context.user_data["attente_mise"] = False
    context.user_data["attente_boost"] = False
    context.user_data["attente_palier"] = False
    context.user_data["attente_message"] = False
    context.user_data["attente_bet"] = False
    context.user_data["attente_cote"] = False
    context.user_data["pari_en_cours"] = None

    if OWNER_ID is None:

        context.user_data["proposition_owner"] = True
        context.user_data["confirmation_reset"] = False

        await update.message.reply_text(
            "⚠️ Le bot doit d'abord identifier le propriétaire.\n\n"
            "Comme tu es propriétaire du canal, réponds :\n\n"
            "**PROPRIETAIRE**"
        )
        return

    if user_id != OWNER_ID:

        await update.message.reply_text(
            "❌ Cette commande est réservée au propriétaire du bot."
        )
        return

    context.user_data["proposition_owner"] = False
    context.user_data["confirmation_reset"] = True

    await update.message.reply_text(
        "⚠️ **RESET TOKEN - LEVEL** ⚠️\n\n"
        "Cette action va supprimer :\n"
        "💰 La mise\n"
        "🪙 Les Tokens\n"
        "📊 Le palier\n"
        "🎲 Le dernier dé\n"
        "🔥 La série de victoires\n"
        "🚀 Les boosts\n\n"
        "❗ Cette action est irréversible.\n\n"
        "Écris **CONFIRMER** pour continuer.",
        parse_mode="Markdown"
    )


# ============================================================
# MESSAGES TEXTE
# ============================================================

async def recevoir_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # --------------------------------------------------------
    # RÉPONSE AU MESSAGE PERSONNALISÉ
    # --------------------------------------------------------

    if context.user_data.get("attente_message"):

        message_personnel = update.message.text

        context.user_data["attente_message"] = False

        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_personnel,
            parse_mode=None
        )

        await update.message.reply_text(
            "✅ Message publié dans le canal !"
        )

        return

    # --------------------------------------------------------
    # RÉPONSE AU BET
    # --------------------------------------------------------

    if context.user_data.get("attente_bet"):

        # On reprend exactement ce que tu écris
        pari = update.message.text.strip()

        if not pari:
            await update.message.reply_text(
                "❌ Le pari ne peut pas être vide.\n\n"
                "Écris simplement ton pari."
            )
            return

        context.user_data["pari_en_cours"] = pari
        context.user_data["attente_bet"] = False
        context.user_data["attente_cote"] = True

        await update.message.reply_text(
            "💰 **QUELLE EST LA COTE ?**\n\n"
            "Exemple : **2.50**\n\n"
            "Tu peux aussi écrire : **2,50** ou **@2.50**"
        )

        return

    # --------------------------------------------------------
    # RÉPONSE À LA COTE DU BET
    # --------------------------------------------------------

    if context.user_data.get("attente_cote"):

        cote_texte = update.message.text.strip()

        # Accepte @2.50, 2.50 et 2,50
        cote_nettoyee = cote_texte.replace("@", "").replace(",", ".")

        try:
            cote = float(cote_nettoyee)

            if cote <= 1:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ Cote invalide.\n\n"
                "Exemples : **2.50**, **2,50** ou **@2.50**"
            )
            return

        pari = context.user_data.get("pari_en_cours")

        if not pari:
            context.user_data["attente_cote"] = False
            await update.message.reply_text(
                "❌ Une erreur est survenue.\n\n"
                "Utilise à nouveau /bet."
            )
            return

        # Sécurise le texte du pari pour HTML
        pari_securise = html.escape(pari)

        message_bet = (
            "🚨🔴 <b>BET EN LIVE</b> 🔴🚨\n\n"
            f"⚽ <b>{pari_securise}</b>\n"
            f"🎯 <b>Cote : @{cote:.2f}</b>\n\n"
            "🪙 <b>On essaie de monter les Tokens !</b> 🚀🔥"
        )

        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_bet,
            parse_mode="HTML"
        )

        context.user_data["attente_cote"] = False
        context.user_data["pari_en_cours"] = None

        await update.message.reply_text(
            "✅ Bet publié dans le canal !"
        )

        return

    texte = update.message.text.replace(",", ".").strip()

    # --------------------------------------------------------
    # CONFIRMATION RESET
    # --------------------------------------------------------

    if context.user_data.get("confirmation_reset"):

        if texte.upper() == "CONFIRMER":

            user_id = update.effective_user.id

            mises.pop(user_id, None)
            tokens.pop(user_id, None)
            paliers_atteints.pop(user_id, None)
            derniers_des.pop(user_id, None)
            victoires_consecutives.pop(user_id, None)
            boost_actif.pop(user_id, None)
            boosts_debloques.pop(user_id, None)

            context.user_data["confirmation_reset"] = False
            context.user_data["attente_mise"] = False
            context.user_data["attente_palier"] = False
            context.user_data["attente_boost"] = False
            context.user_data["attente_message"] = False
            context.user_data["attente_bet"] = False
            context.user_data["attente_cote"] = False
            context.user_data["pari_en_cours"] = None

            message = (
                "🔄 **RESET TOKEN - LEVEL**\n\n"
                "🧹 Profil remis à zéro.\n\n"
                "💰 Mise : aucune\n"
                "🪙 Tokens : 0\n"
                "📊 Palier : 🔰 Départ\n"
                "🎲 Dernier dé : —\n"
                "🔥 Série : 0 victoire\n"
                "🚀 Boost : aucun\n\n"
                "🚀 **Nouveau départ !**"
            )

            await envoyer_au_canal(context, message)

            await update.message.reply_text(
                "✅ Reset effectué et publié dans le canal !"
            )

        else:

            await update.message.reply_text(
                "❌ Reset annulé.\n\n"
                "Écris **CONFIRMER** pour valider."
            )

        return

    # --------------------------------------------------------
    # IDENTIFICATION PROPRIÉTAIRE
    # --------------------------------------------------------

    if context.user_data.get("proposition_owner"):

        if texte.upper() == "PROPRIETAIRE":

            global OWNER_ID

            OWNER_ID = update.effective_user.id

            context.user_data["proposition_owner"] = False

            await update.message.reply_text(
                "✅ Propriétaire enregistré.\n\n"
                "Tu peux maintenant utiliser /reset."
            )

        else:

            await update.message.reply_text(
                "❌ Réponse incorrecte."
            )

        return

    # --------------------------------------------------------
    # RÉPONSE AU BOOST
    # --------------------------------------------------------

    if context.user_data.get("attente_boost"):

        user_id = update.effective_user.id
        serie = victoires_consecutives.get(user_id, 0)

        if texte not in ["2", "3", "10"]:

            await update.message.reply_text(
                "❌ Choix invalide.\n\n"
                "Réponds avec **2**, **3** ou **10**."
            )
            return

        choix = int(texte)

        conditions = {
            2: 3,
            3: 5,
            10: 10,
        }

        victoires_requises = conditions[choix]

        if serie < victoires_requises:

            await update.message.reply_text(
                "🔒 **BOOST VERROUILLÉ** 🔒\n\n"
                f"Il te faut **{victoires_requises} victoires d’affilée** "
                f"pour utiliser le BOOST ×{choix}.\n\n"
                f"🔥 Série actuelle : **{serie}**"
            )
            return

        if user_id not in boosts_debloques:
            boosts_debloques[user_id] = set()

        if victoires_requises not in boosts_debloques[user_id]:

            await update.message.reply_text(
                "❌ Ce boost n'est pas disponible actuellement."
            )
            return

        boost_actif[user_id] = choix

        context.user_data["attente_boost"] = False

        if choix == 2:

            message = (
                "🚀 **BOOST ×2 CHARGÉ !** 🚀\n\n"
                "🪙 **LE PROCHAIN GAIN DE TOKENS SERA DOUBLÉ !** 💥\n\n"
                "🎯 Le boost est prêt.\n"
                "👀 **Il ne reste plus qu'à l'utiliser !**"
            )

        elif choix == 3:

            message = (
                "🚀🚀 **BOOST ×3 CHARGÉ !** 🚀🚀\n\n"
                "🪙 **LE PROCHAIN GAIN DE TOKENS SERA TRIPLÉ !** 💥💥💥\n\n"
                "🔥 La série est en feu.\n"
                "👀 **On va chercher le TRIPLE !**"
            )

        else:

            message = (
                "🚨🚨🚨 **BOOST FUSÉE ×10 CHARGÉ !!!** 🚨🚨🚨\n\n"
                "🚀 **LE PROCHAIN GAIN DE TOKENS SERA MULTIPLIÉ PAR 10 !!!** 🚀\n\n"
                "💣💣💣 **×10 TOKENS !** 💣💣💣\n\n"
                "👑 **LA SÉRIE EST LÉGENDAIRE.**\n"
                "🚀 **ON DÉCOLLE !!!**"
            )

        await envoyer_au_canal(context, message)

        await update.message.reply_text(
            f"✅ BOOST ×{choix} chargé !\n\n"
            f"🪙 Le prochain gain positif de Tokens sera multiplié par ×{choix}."
        )

        return

    # --------------------------------------------------------
    # RÉPONSE À /MISE
    # --------------------------------------------------------

    if context.user_data.get("attente_mise"):

        try:

            montant = float(texte)

            if montant <= 0:
                raise ValueError

            user_id = update.effective_user.id

            mises[user_id] = montant

            context.user_data["attente_mise"] = False

            message = (
                "💰 **MISE MENSUELLE ENREGISTRÉE**\n\n"
                f"💵 Mise de départ : **{montant:.2f} €**\n\n"
                "🚀 Ton profil Token - Level est prêt pour la suite."
            )

            await envoyer_au_canal(context, message)

            await update.message.reply_text(
                "✅ Mise enregistrée et publiée dans le canal !"
            )

        except ValueError:

            await update.message.reply_text(
                "❌ Montant invalide.\n\n"
                "Exemple : 50"
            )

        return

    # --------------------------------------------------------
    # RÉPONSE À /PALIER
    # --------------------------------------------------------

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

        user_id = update.effective_user.id
        mise_actuelle = mises.get(user_id)

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

        message = (
            f"🎯 **PALIER ×{multiplicateur} ATTEINT !**\n\n"
            f"💰 Mise de départ : **{mise_actuelle:.2f} €**\n"
            f"📈 Montant atteint : **{montant_atteint:.2f} €**\n"
            f"💵 Bénéfice : **+{benefice:.2f} €**\n\n"
            f"🔄 Base du mois suivant : **{mise_actuelle:.2f} €**"
        )

        await envoyer_au_canal(context, message)

        await update.message.reply_text(
            "✅ Palier publié dans le canal !"
        )

        return


# ============================================================
# SERVEUR WEB
# ============================================================

threading.Thread(
    target=start_web_server,
    daemon=True
).start()


# ============================================================
# APPLICATION TELEGRAM
# ============================================================

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("mise", mise))
app.add_handler(CommandHandler("palier", palier))
app.add_handler(CommandHandler("rappel", rappel))
app.add_handler(CommandHandler("de", de))
app.add_handler(CommandHandler("calcul", calcul))
app.add_handler(CommandHandler("token", token))
app.add_handler(CommandHandler("profil", profil))
app.add_handler(CommandHandler("gagne", gagne))
app.add_handler(CommandHandler("perdu", perdu))
app.add_handler(CommandHandler("boost", boost))
app.add_handler(CommandHandler("goal", goal))
app.add_handler(CommandHandler("var", var))
app.add_handler(CommandHandler("message", message_personnalise))
app.add_handler(CommandHandler("bet", bet))
app.add_handler(CommandHandler("reset", reset))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        recevoir_message,
    )
)

app.run_polling()
