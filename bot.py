import discord
import os
import json
from os import getenv
import discord.state
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread
from blagues_api import BlaguesAPI
from blagues_api import BlagueType
import random
import requests
import time
from datetime import datetime, timedelta, timezone

load_dotenv()

blagues = BlaguesAPI("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTA1OTEzNTcwMzQ2NTg2OTQyMyIsImxpbWl0IjoxMDAsImtleSI6IllNQzhVMlk0bzh4ZGZPTmtVMzI0b2lja3J2VVdaMzdVZ0RRWlVTSFh4RmxnWktPMjltIiwiY3JlYXRlZF9hdCI6IjIwMjUtMDYtMjJUMTc6MTI6NTkrMDA6MDAiLCJpYXQiOjE3NTA2MTIzNzl9.T0Me9mXyY877vNTB-ytuIZBiaR12GPG57804EZ0qFkk")

app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

ping_loop_running = False

def start_ping_loop(url):
    def loop():
        global ping_loop_running
        ping_loop_running = True
        while ping_loop_running:
            try:
                requests.get(url)
                print("Ping envoyé")
            except Exception as e:
                print(e)
            time.sleep(240)
    Thread(target=loop).start()

print("Lancement du bot")
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

@bot.tree.command(name="stayawake", description="Ne pas utiliser. Accès restreint aux administrateurs.")
async def stayawake(interaction: discord.Interaction):
    global ping_loop_running
    if not ping_loop_running:
        start_ping_loop("https://e6bb125a-e46a-4eff-acef-531d373eb860-00-2l2sj3fbmubyo.janeway.replit.dev")
        await interaction.response.send_message("Le bot va maintenant rester en ligne.", ephemeral=True)
    else:
        await interaction.response.send_message("Le keep aive est déjà actif.", ephemeral=True)

@bot.tree.command(name="sleep", description="Ne pas utiliser. Accès restreint aux administrateurs.")
async def sleep(interaction: discord.Interaction):
    """Désactive le keep alive"""
    global ping_loop_running
    if ping_loop_running:
        ping_loop_running = False
        await interaction.response.send_message("🛑 Le bot pourra maintenant s'endormir.", ephemeral=True)
    else:
        await interaction.response.send_message("😴 Le mode keep alive était déjà désactivé.", ephemeral=True)

# ✅ Check admin
def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user_data(user_id):
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = {"money": 0, "last_daily": None}
        save_data(data)
    return data

def save_user_data(user_id: str, user_data: dict):
    data = load_data()
    data[user_id] = user_data
    save_data(data)

def get_all_data():
    data = load_data()
    return data

@bot.tree.command(name="money", description="Permet de voir son nombre de CtrlCoins")
async def money(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    data = get_user_data(user_id)
    if user_id not in data:
        data[user_id] = {"money": 0, "last_daily": None}
        save_data(data)
    money = data[str(interaction.user.id)]["money"]
    await interaction.response.send_message(f"Vous avez actuellement {money} CtrlCoins.", ephemeral=True)

@bot.tree.command(name="daily", description="Permet de récupérer ses CtrlCoins quotidiens.")
async def daily(interaction:discord.Interaction):
    user_id = str(interaction.user.id)
    data = get_user_data(user_id=user_id)

    if user_id not in data:
        data[user_id] = {"money": 0, "last_daily": None}
        save_data(data)

    now = datetime.now(timezone.utc)
    last_claim_str = data[user_id].get("last_daily")

    if last_claim_str:
        last_claim = datetime.fromisoformat(last_claim_str)
        if now - last_claim < timedelta(hours=24):
            next_time = last_claim + timedelta(hours=24)
            remaining = next_time - now
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes = remainder // 60
            await interaction.response.send_message(f"Vous avez déjà récupéré votre récompense quotidienne. Rechargement dans {hours}h {minutes}min.", ephemeral=True)
            return
        
    reward = random.randint(200, 400)
    data[user_id]["money"] += reward
    data[user_id]["last_daily"] = now.isoformat()
    save_data(data)

    await interaction.response.send_message(f"Vous avez reçu {reward} CtrlCoins en récompense quotidienne.", ephemeral=True)

items = {
    "Argent X2": {"price": 500, "type": "role", "role_id": 1394268096486707334}
}

import discord
from discord import app_commands
from discord.ext import commands

class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label=item,
                description=f"{data['price']} CtrlCoins",
                value=item
            )
            for item, data in items.items()
        ]
        super().__init__(placeholder="Choisis un objet à acheter", options=options, min_values=1, max_values=1)
        self.selected_item = None

    async def callback(self, interaction: discord.Interaction):
        self.selected_item = self.values[0]
        await interaction.response.send_message(
            f"✅ Tu as sélectionné **{self.selected_item}**. Clique sur 'Acheter' pour valider.",
            ephemeral=True
        )

class ShopView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.select_menu = ShopSelect()
        self.add_item(self.select_menu)

        self.buy_button = discord.ui.Button(label="Acheter", style=discord.ButtonStyle.green)
        self.buy_button.callback = self.buy_callback
        self.add_item(self.buy_button)

    async def buy_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Pas ton shop bro.", ephemeral=True)
            return

        item_name = self.select_menu.selected_item
        if not item_name:
            await interaction.response.send_message("❗ Sélectionne un objet avant d'acheter.", ephemeral=True)
            return

        item = items[item_name]
        price = item["price"]
        user_id = str(interaction.user.id)

        all_data = get_all_data()
        money = all_data.get(user_id, {}).get("money", 0)

        if money < price:
            await interaction.response.send_message(f"❌ Pas assez de CtrlCoins ! Il te faut {price}.", ephemeral=True)
            return

        # Déduction du prix
        all_data[user_id]["money"] -= price
        save_data(all_data)

        # Si c’est un rôle, on l’ajoute
        if item["type"] == "role":
            role = interaction.guild.get_role(item["role_id"])
            if not role:
                await interaction.response.send_message("⚠️ Rôle introuvable.", ephemeral=True)
                return

            if role in interaction.user.roles:
                await interaction.response.send_message("🟡 Tu as déjà ce rôle.", ephemeral=True)
                return

            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"✨ Tu as acheté le rôle **{role.name}** pour {price} CtrlCoins !",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f"🎉 Tu as acheté **{item_name}** pour {price} CtrlCoins !",
                ephemeral=True
            )

@bot.tree.command(name="shop", description="Permet d'afficher la boutique de CtrlCoins.")
async def shop(interaction: discord.Interaction):
    view = ShopView(interaction.user.id)
    await interaction.response.send_message("🛒 **Bienvenue dans le shop !**", view=view, ephemeral=True)

@bot.tree.command(name="addcoins", description="Permet de donner des CtrlCoins à un membre. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def addcoins(interaction: discord.Interaction, member: discord.Member, ctrlcoins: int):
    user_id = str(member.id)
    all_data = get_all_data()

    # Vérifie si le membre existe dans la base, sinon on crée
    if user_id not in all_data:
        all_data[user_id] = {"money": 0, "last_daily": None}

    all_data[user_id]["money"] += ctrlcoins
    save_data(all_data)

    await interaction.response.send_message(
        f"💰 {ctrlcoins} CtrlCoins ont été ajoutés à {member.mention}. Il a maintenant {all_data[user_id]['money']} CtrlCoins.",
        ephemeral=True
    )

@bot.tree.command(name="removecoins", description="Permet de retirer des CtrlCoins à un membre. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def removecoins(interaction: discord.Interaction, member: discord.Member, ctrlcoins: int):
    user_id = str(member.id)
    all_data = get_all_data()

    # Assure que le membre a une entrée sinon init
    if user_id not in all_data:
        all_data[user_id] = {"money": 0, "last_daily": None}

    all_data[user_id]["money"] = max(0, all_data[user_id]["money"] - ctrlcoins)
    save_data(all_data)

    await interaction.response.send_message(
        f"💸 {ctrlcoins} CtrlCoins ont été retirés à {member.mention}. Il lui reste maintenant {all_data[user_id]['money']} CtrlCoins.",
        ephemeral=True
    )

@bot.tree.command(name="defcoins", description="Permet de définir le nombre de CtrlCoins d'un membre. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def defcoins(interaction: discord.Interaction, member: discord.Member, ctrlcoins: int):
    user_id = str(member.id)
    all_data = get_all_data()

    # Vérifie si le membre existe dans la base, sinon on crée
    if user_id not in all_data:
        all_data[user_id] = {"money": 0, "last_daily": None}

    all_data[user_id]["money"] = ctrlcoins
    save_data(all_data)

    await interaction.response.send_message(f"{member.mention} a maintenant {all_data[user_id]['money']} CtrlCoins.", ephemeral=True)

@bot.tree.command(name="seasonreset", description="Ne pas missclick !!! Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def seasonreset(interaction: discord.Interaction):
    data = get_all_data()
    data.clear()

# ✅ Sync des slash commands
@bot.event
async def on_ready():
    print("Bot activé !")
    try:
        synced = await bot.tree.sync()
        print(f"Commandes slash synchronisées : {len(synced)}")
    except Exception as e:
        print(e)

# ✅ Message classique "bonjour"
# @bot.event
# async def on_message(message: discord.Message):
#     if message.author.bot:
#         return
#     if message.content.lower() == "bonjour":
#         await message.channel.send("Bonjour à Titouan")

class TwitchNotifButtonView(discord.ui.View):

    def __init__(self, roleTwitchNotif: discord.Role, member: discord.Member):
        super().__init__()
        self.roleTwitchNotif = roleTwitchNotif
        self.member = member

    @discord.ui.button(label="Oui", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.member.add_roles(self.roleTwitchNotif)
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="Vous recevrez maintenant les notifications des live Twitch sur le serveur.",
            view=self
        )

    @discord.ui.button(label="Non", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content="Vous ne recevrez pas les notifications des live Twitch mais vous pourrez toujour les activer en réagissant au message épinglé dans le salon dédié.",
            view=self
        )

@bot.event
async def on_member_join(member: discord.Member):

    ctrlRole = discord.utils.get(member.guild.roles, name="Commu-Ctrl")

    if "ctrl" in member.name.lower() :
        await member.add_roles(ctrlRole)

    roleTwitchNotif = member.guild.get_role(1390017660216938636)

    view = TwitchNotifButtonView(roleTwitchNotif=roleTwitchNotif, member=member)

    await member.send("Bienvenue dans le serveur de la team CTRL, voulez-vous recevoir des notifications lorsque CtrlZed ou CtrlMeta lance un live ?", view=view)

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and not message.author.bot:
        print(f"[DM] {message.author}: {message.content}")
        
        if message.content.lower() == "oui" or message.content.lower() == "yes":
            guild = bot.get_guild(1305287871648895048)
            role = guild.get_role(1390017660216938636)
            member = guild.get_member(message.author.id)
            if member:
                await member.add_roles(role)
                await message.channel.send("Vous recevrez maintenant les notifications de twitch !")

        elif message.content.lower() == "non" or message.content.lower() == "no":
            await message.channel.send("Très bien, vous ne recevrez pas les notifications de twitch sur le serveur mais si vous changez d'avis, vous pourrez activer le rôle réaction en message épinglé dans le salon notif-twitch.")

        else:
            await message.channel.send(f"Je ne comprend pas ce mot : '{message.content}'")

    await bot.process_commands(message)

@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):

    ctrlRole = discord.utils.get(after.guild.roles, name="Commu-Ctrl")

    if ctrlRole is None:
        return  # Le rôle n'existe pas

    name_before = (before.nick or before.name).lower()
    name_after = (after.nick or after.name).lower()

    # Si "ctrl" a été ajouté dans le nom
    if "ctrl" in name_after and "ctrl" not in name_before:
        if ctrlRole not in after.roles:
            await after.add_roles(ctrlRole)

    # Si "ctrl" a été retiré du nom
    elif "ctrl" not in name_after and "ctrl" in name_before:
        if ctrlRole in after.roles:
            await after.remove_roles(ctrlRole)

# ✅ Slash command /twitch
@bot.tree.command(name="twitch", description="Affiche le lien de ma chaîne Twitch.")
async def twitch(interaction: discord.Interaction):
    zed = await interaction.guild.fetch_member(1059135703465869423)
    meta = await interaction.guild.fetch_member(1165316767611105356)
    await interaction.response.send_message(f"Lien de la chaîne twitch de {zed.mention} : https://twitch.tv/ctrlzed24 \n Lien de la chaîne twitch de {meta.mention} : https://twitch.tv/ctrlmeta23")

# ✅ Slash command /cdp
@bot.tree.command(name="cdp", description="Permet d'envoyer un avertissement à un membre. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def cdp(interaction: discord.Interaction, member: discord.Member, reason: str):
    guild = interaction.guild
    cdp_role = discord.utils.get(guild.roles, name="cdp")

    # ✅ Vérifie s’il a déjà le rôle CDP
    if cdp_role in member.roles:
        await interaction.response.send_message("Avertissement envoyé et utilisateur **banni** !")
        await member.send(f"C'est votre deuxième **avertissement** c'est pour cela que vous avez été banni du serveur. Raison : {reason}")
        await member.ban()
    else:
        await member.send(f"Vous vous êtes pris un **avertissement**, faites attention à respecter le règlement. Raison : {reason}")
        await interaction.response.send_message("Avertissement envoyé !")
        await member.add_roles(cdp_role)

@bot.tree.command(name="ban", description="Permet de bannir un utilisateur. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str) :
    member_mention = await interaction.guild.fetch_member(member.id)
    await interaction.response.send_message(f"{member_mention.mention} a été banni.", ephemeral=True)
    await member.send(f"Vous avez été banni du serveur. Raison : {reason}")
    await member.ban(reason=reason)

@bot.tree.command(name="unban", description="Permet de débannir un utilisateur. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ {user.display_name} a été débanni.", ephemeral=True)
    except discord.NotFound:
        await interaction.response.send_message("❌ Utilisateur non trouvé ou pas banni.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de débannir cet utilisateur.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

@bot.tree.command(name="teamate", description="Permet de trouver un coéquipier sur le jeu de votre choix.")
async def teamate(interaction: discord.Interaction, game: str):
    file = discord.File("./manetteBotDiscord.jpg", filename="manette.jpg")
    embed = discord.Embed(
        title="Demande de teamate !",
        color=discord.Color.green(),
        description=f"{interaction.user.display_name} recherche des coéquipiers. Qui veut jouer avec lui ?"
    )
    embed.add_field(name="Jeu", value=game, inline=False)
    embed.set_image(url='attachment://manette.jpg')
    await interaction.response.send_message(embed=embed, file=file)

@bot.tree.command(name="help", description="Permet d'aider les utilisateur à comprendre les fonctionnalités du bot.")
async def help(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Mode d'emploi de CtrlBot.",
        description="Voici un mode d'emploi complet pour savoir utiliser CtrlBot",
        color=discord.Color.green()
    )
    for command in bot.tree.get_commands():
        if interaction.user.guild_permissions.administrator:
            embed.add_field(name=f"/{command.name.capitalize()}", value=command.description, inline=True)
        elif "Accès restreint aux administrateurs." in command.description:
            continue
        else:
            embed.add_field(name=f"/{command.name.capitalize()}", value=command.description, inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# class PlateformeSelect(discord.ui.Select):
#     def __init__(self):
#         options = [
#             discord.SelectOption(label="PC", emoji="🖥️", description="Je joue sur PC"),
#             discord.SelectOption(label="PlayStation", emoji="🎮", description="Je joue sur PS"),
#             discord.SelectOption(label="Xbox", emoji="🕹️", description="Je joue sur Xbox"),
#         ]
#         super().__init__(
#             placeholder="Choisis ta plateforme...",
#             min_values=1,
#             max_values=1,
#             options=options,
#         )

#     async def callback(self, interaction: discord.Interaction):
#         await interaction.response.send_message(
#             f"Tu as choisi **{self.values[0]}** ✅", ephemeral=True
#         )

# La view qui contient le menu
# class PlateformeView(discord.ui.View):
#     def __init__(self):
#         super().__init__()
#         self.add_item(PlateformeSelect())

# @bot.tree.command(name="menu", description="commande de test menu déroulants")
# async def menu(interaction: discord.Interaction):
#     await interaction.response.send_message(view=PlateformeView())

@bot.tree.command(name="report", description="Permet de signaler un membre du serveur aux administrateurs.")
async def report(interaction: discord.Interaction, member: discord.Member, reason: str, temoin1: discord.Member = None, temoin2: discord.Member = None, temoin3: discord.Member = None):
    await interaction.response.send_message("Signalement envoyé aux administarteurs.", ephemeral=True)
    await interaction.guild.get_channel(1383859853293916221).send(f"{interaction.user.mention} a signalé {member.mention}, les témoins sont {temoin1.mention}, {temoin2.mention} et {temoin3.mention}")

@bot.tree.command(name="getout", description="Permet de kick un membre du serveur. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def getout(interaction: discord.Interaction, member: discord.Member, reason: str):
    await interaction.response.send_message(f"{member.mention} a été expulsé du serveur.", ephemeral=True)
    await member.send(f"Vous avez été expulsé du serveur. Raison : {reason}")
    await member.kick(reason=reason)

@bot.tree.command(name="recrutement", description="Permet d'envoyer un message au administrateurs pour devenir modérateur du serveur.")
async def recrutement(interaction: discord.Interaction, motivation: str):
    await interaction.response.send_message("Message envoyé aux administrateurs, ils vont regarder votre demande dès que possible.", ephemeral=True)
    zed = await interaction.guild.fetch_member(1059135703465869423)
    meta = await interaction.guild.fetch_member(1165316767611105356)
    await zed.send(f"{interaction.user.display_name} fait une demande pour devenir modérateur sur le serveur. Voici ses motivations : {motivation}")
    await meta.send(f"{interaction.user.display_name} fait une demande pour devenir modérateur sur le serveur. Voici ses motivations : {motivation}")

@bot.tree.command(name="blague", description="Permet d'afficher une blague.")
async def blague(interaction: discord.Interaction):
    import random

    categorie = random.choice(["dev", "global"])
    blague = await blagues.random_categorized(categorie)

    # Si c'est une blague avec réponse (type dev)
    if blague.answer:
        message = f"{blague.joke}\n||{blague.answer}||"  # Spoiler pour l'effet surprise
    else:
        message = blague.joke

    await interaction.response.send_message(message)

@bot.tree.command(name="rename", description="Permet de se renommer sur le serveur")
async def rename(intercation: discord.Interaction, name: str):
    try:
        await intercation.user.edit(nick=name)
        await intercation.response.send_message(f"✅ Ton pseudo a été changé en **{name}**")
    except discord.Forbidden:
        await intercation.response.send_message("❌ J'ai pas la permission de te rename !")
    except Exception as e:
        await intercation.response.send_message(f"⚠️ Une erreur est survenue : {e}")

@bot.tree.command(name="adminrename", description="Permet de renommer un utilisateur sur le serveur. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def adminrename(intercation: discord.Interaction, member: discord.Member, name: str):
    await intercation.response.send_message(f"Le pseudo de {member.mention} sur le serveur est maintenant {name}", ephemeral=True)
    await member.edit(nick=name)

class EventButton(discord.ui.View):

    def __init__(self, participantsMax: int, name: str):
        super().__init__()
        self.name = name
        self.participantsMax = participantsMax
        self.participants = []

    @discord.ui.button(label="Participer 🎉", style=discord.ButtonStyle.primary)
    async def participate(self, interaction: discord.Interaction, button: discord.Button):
        button.disabled = True

        user = interaction.user

        if user in self.participants:
            await interaction.response.send_message("Vous participez déjà à cet event !", ephemeral=True)
            return
        
        if len(self.participants) >= self.participantsMax:
            await interaction.response.send_message("L'event est au complet, désolé.", ephemeral=True)
            return

        self.participants.append(user)

        if len(self.participants) >= self.participantsMax:
            button.disabled = True
            await interaction.message.edit(content="L'event est au complet, mais tkt y en aura d'autres.", view=self)
            modChannel = await interaction.guild.get_channel(1383859853293916221)
            await modChannel.send(f"L'event {self.name} est au complet, voici les participants")
            for participant in self.participants:
                await modChannel.send(participant.display_name)

        await interaction.response.send_message("Vous participez maintenant à l'event.", ephemeral=True)

@bot.tree.command(name="event", description="Permet de créer des évènements. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def event(interaction: discord.Interaction, participants: int, nom: str, categorie: str):
    embed = discord.Embed(color=discord.Color.blue(), title="Un event vient d'être lancé !")
    embed.add_field(name="Nom", value=nom)
    embed.add_field(name="Catégorie", value=categorie)
    embed.add_field(name="Participants Max", value=str(participants))
    view = EventButton(participantsMax=participants, name=nom)
    await interaction.response.send_message(embed=embed, view=view)

# @bot.tree.command(name="clear", description="Permet de clear le channel dans lequel la commande est lancée. Accès restreint aux administrateurs.")
# @app_commands.check(is_admin)
# async def clear(interaction: discord.Interaction):
#     await interaction.channel.purge(limit=None)

# ✅ Gérer les erreurs de permission des slash commands
@bot.tree.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Vous n'avez pas les permissions pour exécuter cette commande.", ephemeral=True)

@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"❌ Une erreur est survenue : {error}")

keep_alive()
# ✅ Lancement du bot
bot.run(getenv('DISCORD_TOKEN'))
