import discord
from discord import message
from discord import user
from discord.ext import commands, tasks
import random
from discord.ext.commands.bot import Bot
import youtube_dl
import asyncio
from discord_slash import ButtonStyle
from discord_slash.utils.manage_components import *
import datetime

bot = commands.Bot(command_prefix = "!", description = "MitsuPy")
status = ["!help",
		"Mitsu Py",
		"Dev on python"]
musics = {}
ytdl = youtube_dl.YoutubeDL()


class Video:
    def __init__(self, link):
        video = ytdl.extract_info(link, download=False)
        video_format = video["formats"][0]
        self.url = video["webpage_url"]
        self.stream_url = video_format["url"]

@bot.command()
async def leave(ctx):
    client = ctx.guild.voice_client
    await client.disconnect()
    musics[ctx.guild] = []

@bot.command()
async def resume(ctx):
    client = ctx.guild.voice_client
    if client.is_paused():
        client.resume()


@bot.command()
async def pause(ctx):
    client = ctx.guild.voice_client
    if not client.is_paused():
        client.pause()


@bot.command()
async def skip(ctx):
    client = ctx.guild.voice_client
    client.stop()


def play_song(client, queue, song):
    source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(song.stream_url
        , before_options = "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"))

    def next(_):
        if len(queue) > 0:
            new_song = queue[0]
            del queue[0]
            play_song(client, queue, new_song)
        else:
            asyncio.run_coroutine_threadsafe(client.disconnect(), bot.loop)

    client.play(source, after=next)


@bot.command()
async def play(ctx, url):
    print("play")
    client = ctx.guild.voice_client

    if client and client.channel:
        video = Video(url)
        musics[ctx.guild].append(video)
    else:
        channel = ctx.author.voice.channel
        video = Video(url)
        musics[ctx.guild] = []
        client = await channel.connect()
        await ctx.send(f"Je lance : {video.url}")
        play_song(client, musics[ctx.guild], video)





@bot.event
async def on_ready():
	print("Ready !")
	changeStatus.start()

@bot.command()
async def start(ctx, secondes = 5):
	changeStatus.change_interval(seconds = secondes)

@tasks.loop(seconds = 5)
async def changeStatus():
	game = discord.Game(random.choice(status))
	await bot.change_presence(status = discord.Status.dnd, activity = game)






#coucou (test de première commande)
@bot.command()
async def coucou(ctx):
	await ctx.send("Coucou !")

#say
@bot.command()
async def serverInfo(ctx):
	server = ctx.guild
	numberOfTextChannels = len(server.text_channels)
	numberOfVoiceChannels = len(server.voice_channels)
	serverDescription = server.description
	numberOfPerson = server.member_count
	serverName = server.name
	message = f"Le serveur **{serverName}** contient *{numberOfPerson}* personnes ! \nLa description du serveur est {serverDescription}. \nCe serveur possède {numberOfTextChannels} salons écrit et {numberOfVoiceChannels} salon vocaux."
	await ctx.send(message)



@bot.command()
async def say(ctx, *args):
        print(args)
        await ctx.send(" ".join(args))



#clear
@bot.command()
@commands.has_permissions(manage_messages = True)
async def clear(ctx, nombre : int):
    messages = await ctx.channel.history(limit = nombre + 1).flatten()
    for message in messages:
        await message.delete()
        print("clear de :", message)

#kick
@bot.command()
@commands.has_permissions(kick_members = True)
async def kick(ctx, user : discord.User, *reason):
    reason = " ".join(reason)
    print("kick pour :", reason)
    await ctx.guild.kick(user, reason = reason)
    await ctx.send(f"{user} a été kick pour **{reason}**")
#ban
@bot.command()
@commands.has_permissions(ban_members = True)
async def ban(ctx, user : discord.User, *reason):
    reason = " ".join(reason)
    print("ban pour :", reason)
    await ctx.guild.ban(user, reason = reason)
    await ctx.send(f"{user} a été ban pour **{reason}**")


#unban
@bot.command()
@commands.has_permissions(ban_members = True)
async def unban(ctx, user, *reason):
	reason = " ".join(reason)
	userName, userId = user.split("#")
	bannedUsers = await ctx.guild.bans()
	for i in bannedUsers:
		if i.user.name == userName and i.user.discriminator == userId:
			await ctx.guild.unban(i.user, reason = reason)
			await ctx.send(f"{user} à été unban.")
			return
	await ctx.send(f"L'utilisateur {user} n'est pas banni.")

    #banlist
@bot.command()
async def banlist(ctx):
	ids = []
	bans = await ctx.guild.bans()
	for i in bans:
		ids.append(str(i.user.id))
	await ctx.send("Voici la liste des utilisateurs banni sur ce serveur :")
	await ctx.send("\n".join(ids))

    #help (embed)

@bot.command()
async def helptest(ctx):
    embed = discord.Embed(title = "Voici la page **Help**", description = "`Ban` : **Bannir un membre.**\n\n*!ban @user*\n\n`Kick` : **Expulser un membre.**\n\n*!kick @user*\n\n`Unban` : **Dé-bannir un membre.**\n\n*!unban MitsuPy#0999*\n\n`Clear` : **Supprimer des messages.**\n\n*!clear 10*\n\n`Banlist` : **Voir la liste des membres banni.**\n\n*!banlist*\n\n`Say` : **Faire parler le bot avec un/une message/phrase choisi.**\n\n*!say test de la commande*\n\n`Play` : **Faire jouer une musique.**\n\n*!play https://youtube.com/votremusique*\n\n`Skip` : **Passer la musique.**\n\n*!skip*\n\n`Pause` : **Mettre en pause la musique.**\n\n*!pause*\n\n`Resume` : **Faire un résumé de la musique.**\n\n*!resume*\n\n`Leave` : **Faire quitter le bot du salon vocal**\n\n*!leave*")
    await ctx.send(embed = embed)    
    

async def createMutedRole(ctx):
    mutedRole = await ctx.guild.create_role(name = "Muted",
                                            permissions = discord.Permissions(
                                                send_messages = False,
                                                speak = False),
                                            reason = "Creation du role Muted pour mute des gens.")
    for channel in ctx.guild.channels:
        await channel.set_permissions(mutedRole, send_messages = False, speak = False)
    return mutedRole

async def getMutedRole(ctx):
    roles = ctx.guild.roles
    for role in roles:
        if role.name == "Muted":
            return role
    
    return await createMutedRole(ctx)
#mute
@bot.command()
async def mute(ctx, member : discord.Member, *, reason = "Aucune raison n'a été donné."):
    mutedRole = await getMutedRole(ctx)
    await member.add_roles(mutedRole, reason = reason)
    await ctx.send(f"{member.mention} a été mute !")
#unmute
@bot.command()
async def unmute(ctx, member : discord.Member, *, reason = "Aucune raison n'a été donné."):
    mutedRole = await getMutedRole(ctx)
    await member.remove_roles(mutedRole, reason = reason)
    await ctx.send(f"{member.mention} a été unmute !")




#bouton et menu select

@bot.command()
async def choix(ctx):
    buttons = [
        create_button(
            style=ButtonStyle.blue,
            label="Choisissez moi",
            custom_id="oui"
        ),
        create_button(
            style=ButtonStyle.danger,
            label="Prend moi nan ?",
            custom_id="non"
        )
    ]
    action_row = create_actionrow(*buttons)
    fait_choix = await ctx.send("Faites votre choix !", components=[action_row])

    def check(m):
        return m.author_id == ctx.author.id and m.origin_message.id == fait_choix.id

    button_ctx = await wait_for_component(bot, components=action_row, check=check)
    if button_ctx.custom_id == "oui":
        await button_ctx.edit_origin(content="Bravo !")
    else:
        await button_ctx.edit_origin(content="Il ne fallait pas cliquer ici..")


@bot.command()
@commands.has_permissions(manage_messages = True)
async def gstart(ctx, mins : int, * , prize: str):
    embed = discord.Embed(title = "Réagissez avec <a:emoji:882428659972079636> pour participer\n*Nombre de gagnants : 1*", description = f"{ctx.author.mention} *souhaite donner* : **{prize}**", color = ctx.author.color)
    
    end = datetime.datetime.utcnow() + datetime.timedelta(seconds = mins*60)

    embed.add_field(name = "Finis dans :", value = f"{mins} secondes")
    embed.add_field(name = "A commencé il y a :", value = f"{mins} secondes")
    embed.set_footer(text = "Mitsu Py")

    my_msg = await ctx.send(embed = embed)
    
    await my_msg.add_reaction("<a:emoji:882428659972079636>")

    await asyncio.sleep(mins)

    new_msg = await ctx.channel.fetch_message(my_msg.id)

    users = await new_msg.reactions[0].users().flatten()
    users.pop(users.index(bot.user))

    winner = random.choice(users)

    await ctx.send(f"Bravo {winner.mention} tu as gagné **{prize}** !")



@bot.command()
@commands.has_permissions(manage_messages = True)
async def gcreate(ctx):
   

    
    giveaway_questions = ['Dans quel salon le giveaway va se dérouler ?', 'Quel est le prix du giveaway ?', 'Combien de temps durera t-il ? (en secondes)',]
    giveaway_answers = []


    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel
    
   
    for question in giveaway_questions:
        await ctx.send(question)
        try:
            message = await bot.wait_for('message', timeout= 30.0, check= check)
        except asyncio.TimeoutError:
            await ctx.send('Vous n\'avez pas répondu à temps.')
            return
        else:
            giveaway_answers.append(message.content)

    try:
        c_id = int(giveaway_answers[0][2:-1])
    except:
        await ctx.send(f'Mentionner le channel correctement.  Comme ceci : {ctx.channel.mention}')
        return
    
  
    channel = bot.get_channel(c_id)
    prize = str(giveaway_answers[1])
    time = int(giveaway_answers[2])

    await ctx.send(f'Le giveaway pour : {prize} va bientôt commencer\nCe giveaway finira dans {time} secondes.')

   
    give = discord.Embed(color = 0x000000)
    give.set_author(name = f'Nouveau Giveaway !!')
    give.add_field(name= f' Prix : {prize} !', value = f'*Réagissez avec <a:emoji:882428659972079636> pour participer* !\n Fin dans : {time} secondes !', inline = False)
    end = datetime.datetime.utcnow() + datetime.timedelta(seconds = time)
    give.set_footer(text = f'Giveaway par : {ctx.author.name}')
    my_message = await channel.send(embed = give)
    
    
    await my_message.add_reaction("<a:emoji:882428659972079636>")
    await asyncio.sleep(time)

    new_message = await channel.fetch_message(my_message.id)

    
    users = await new_message.reactions[0].users().flatten()
    users.pop(users.index(bot.user))
    winner = random.choice(users)

    
    await channel.send(f"Bravo {winner.mention} tu as gagné **{prize}** !")






@bot.command()
@commands.has_role("Giveaway")
async def reroll(ctx, channel: discord.TextChannel, id_ : int):
    # Reroll command requires the user to have a "Giveaway Host" role to function properly
    try:
        new_message = await channel.fetch_message(id_)
    except:
        await ctx.send("Id incorrect.")
        return
    
    # Picks a new winner
    users = await new_message.reactions[0].users().flatten()
    users.pop(users.index(bot.user))
    winner = random.choice(users)

    # Announces the new winner to the server
    reroll_announcement = discord.Embed(color = 0xff2424)
    reroll_announcement.set_author(name = f'Le giveaway a été reroll !')
    reroll_announcement.add_field(name = f'Nouveau gagnant :', value = f'{winner.mention}', inline = False)
    await channel.send(embed = reroll_announcement)



bot.run("OTAzMDg5MDMxMDg3Mjg4Mzcx.YXn5Mw.HWQABF_7AqbpIgcyWis_5dFtRD0")



