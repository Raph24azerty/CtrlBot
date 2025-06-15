import discord
from os import getenv
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Le bot est en ligne"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

load_dotenv()

print("Lancement du bot")
bot = commands.Bot(command_prefix="/", intents=discord.Intents.all())

# ✅ Check admin
def is_admin(interaction: discord.Interaction):
    return interaction.user.guild_permissions.administrator

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
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.content.lower() == "bonjour":
        await message.channel.send("Bonjour à Titouan")

@bot.event
async def on_member_join(member: discord.Member):

    ctrlRole = discord.utils.get(member.guild.roles, name="Commu-Ctrl")

    if "ctrl" in member.name.lower() :
        await member.add_roles(ctrlRole)

@bot.event
async def on_member_update(member: discord.Member):

    ctrlRole = discord.utils.get(member.guild.roles, name="Commu-Ctrl")

    if "ctrl" in member.name.lower() :
        await member.add_roles(ctrlRole)

# ✅ Slash command /twitch
@bot.tree.command(name="twitch", description="Affiche le lien de ma chaîne Twitch.")
async def twitch(interaction: discord.Interaction):
    zed = await interaction.guild.fetch_member(1059135703465869423)
    meta = await interaction.guild.fetch_member(1165316767611105356)
    await interaction.response.send_message(f"Lien de la chaîne twitch de {zed.mention} : https://twitch.tv/ctrlzed24 \n Lien de la chaîne twitch de {meta.mention} : https://twitch.tv/zo_loucab_17")

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
    await interaction.response.send_message(f"{member_mention.mention} banni.")
    await member.send(f"Vous avez été banni du serveur. Raison : {reason}")
    await member.ban()

@bot.tree.command(name="unban", description="Permet de débannir un utilisateur. Accès restreint aux administrateurs.")
@app_commands.check(is_admin)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user_id = int(user_id)
        user = await bot.fetch_user(user_id)
        await interaction.guild.unban(user)
        await interaction.response.send_message(f"✅ {user.display_name} a été débanni.")
    except discord.NotFound:
        await interaction.response.send_message("❌ Utilisateur non trouvé ou pas banni.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Je n'ai pas la permission de débannir cet utilisateur.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Erreur : {e}", ephemeral=True)

@bot.tree.command(name="teamate", description="Permet de trouver un coéquipier sur le jeu de votre choix.")
async def teamate(interaction: discord.Interaction, game: str):
    file = discord.File("assets/manetteBotDiscord.jpg", filename="manette.jpg")
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
        embed.add_field(name=f"/{command.name.capitalize()}", value=command.description, inline=True)

    await interaction.response.send_message(embed=embed, ephemeral=True)

class PlateformeSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="PC", emoji="🖥️", description="Je joue sur PC"),
            discord.SelectOption(label="PlayStation", emoji="🎮", description="Je joue sur PS"),
            discord.SelectOption(label="Xbox", emoji="🕹️", description="Je joue sur Xbox"),
        ]
        super().__init__(
            placeholder="Choisis ta plateforme...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Tu as choisi **{self.values[0]}** ✅", ephemeral=True
        )

# La view qui contient le menu
class PlateformeView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(PlateformeSelect())

@bot.tree.command(name="menu", description="commande de test menu déroulants")
async def menu(interaction: discord.Interaction):
    await interaction.response.send_message(view=PlateformeView())

@bot.tree.command(name="report", description="Permet de signaler un membre du serveur aux administrateurs.")
async def report(interaction: discord.Interaction, member: discord.Member, reason: str, temoin1: discord.Member = None, temoin2: discord.Member = None, temoin3: discord.Member = None):
    await interaction.response.send_message("Signalement envoyé aux administarteurs.", ephemeral=True)
    await interaction.guild.get_channel(1383859853293916221).send(f"{interaction.user.mention} a signalé {member.mention}, les témoins sont {temoin1.mention}, {temoin2.mention} et {temoin3.mention}")

# ✅ Gérer les erreurs de permission des slash commands
@bot.tree.error
async def admin_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message("❌ Vous n'avez pas les permissions pour exécuter cette commande.", ephemeral=True)

keep_alive()
# ✅ Lancement du bot
bot.run(getenv('DISCORD_TOKEN'))
