import requests
import discord
import json
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks
from discord import Embed

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

with open('config.json') as f:
    config = json.load(f)

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
    
    async def on_ready(self):
        await self.tree.sync()
        print("Successfully synced commands")
        print(f"Logged onto {self.user}")

bot = Bot()
rotation = []
timeToTimeout = 0

@bot.command(name="commands", description="Displays command information.")
async def help(ctx):
    embed = Embed(title="Command Information", description="Here are the available commands:", color=0x00ff00)
    embed.add_field(name="!rotation-add {username}", value="Add a user that is in the current channel to the rotation.", inline=False)
    embed.add_field(name="!rotation-remove {username}", value="Remove a user that is in the channel from the rotation.", inline=False)
    embed.add_field(name="!rotation-info", value="Print out the current rotation.", inline=False)
    embed.add_field(name="!rotation-clear", value="Clear the current rotation.", inline=False)
    embed.add_field(name="!chain-timer", value="Print out information about the factions current chain.", inline=False)
    embed.add_field(name="!chain-start {seconds}", value="Start a loop where the current rotation and chain information will be printed every n seconds(default 30).", inline=False)
    embed.add_field(name="!chain-stop", value="Stop the loop.", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="chain-start", description="Starts the chain.")
async def handle_chain_start(ctx):
    try:
        seconds = float(ctx.message.content.split(' ')[1])
    except IndexError:
        seconds = 30.0
    if seconds < 30:
        await ctx.send(content=f'Interval should be at least 30 seconds.')
        return
    chain_task.change_interval(seconds=seconds)
    chain_task.start(ctx)

@bot.command(name="chain-stop", description="Stops the chain.")
async def handle_chain_stop(ctx):
    chain_task.cancel()
    await ctx.send(content=f'Timer stopped, use !chain-start to start again.')

@bot.command(name="chain-timer", description="Prints chain information.")
async def get_faction_chain_timer(ctx):
    print("Checking chain timer")
    url = f'https://api.torn.com/faction/?selections=chain&key={config["TORN_API_KEY"]}'
    response = requests.get(url).json()
    timeout = response['chain']['timeout']
    current = response['chain']['current']
    check_and_rotate_if_time_to_timeout_decreased(timeout)
    global timeToTimeout
    timeToTimeout = timeout
    await ctx.send(content=f'Faction chain count: {current}, time remaining: {timeout} seconds.')

@bot.command(name="rotation-add", description="Adds a user to the rotation.")
async def handle_rotation_add(ctx):
    try:
        user = await get_and_validate_member(ctx)
        await add_user_to_rotation(user, ctx)
        await rotation_info(ctx)
    except Exception as error:
        print(f"Error fetching user: {error}")
        return

@bot.command(name="rotation-clear", description="Clears the rotation.")
async def clear_rotation(ctx):
    print("Clearing rotation")
    global rotation
    rotation = []
    await ctx.send(content="Rotation cleared")

@bot.command(name="rotation-info", description="Prints chain information.")
async def rotation_info(ctx):
    rotation_usernames = [f"{i+1}. {member.name}" for i, member in enumerate(rotation)]
    rotation_str = '\n'.join(rotation_usernames)
    embed = Embed(title="Current rotation", description="This is the current rotation:", color=0x00ff00)
    embed.add_field(name="Current rotation:", value=rotation_str, inline=False)
    await ctx.send(embed=embed)
    
@bot.command(name="rotation-remove", description="Removes a user from the rotation.")
async def handle_rotation_remove(ctx):
    try:
        user = await get_and_validate_member(ctx)
        await remove_user_from_rotation(user, ctx)
        await rotation_info(ctx)
    except Exception as error:
        print(f"Error fetching user: {error}")
        return

@tasks.loop(seconds=30)
async def chain_task(ctx):
    await start_rotation_info(ctx)

async def start_rotation_info(ctx):
    await rotation_info(ctx)
    await get_faction_chain_timer(ctx)

async def remove_user_from_rotation(user, ctx):
    if user not in rotation:
        await ctx.send(f'{user.name} is not in the rotation.')
        return
    rotation.remove(user)

async def add_user_to_rotation(user, ctx):
    if user in rotation:
        await ctx.send(f'{user.name} is already in the rotation.')
        return
    rotation.append(user)

async def get_and_validate_member(ctx):
    username = ctx.message.content.split(' ')[1]
    member = await ctx.guild.query_members(query=username);
    first_member = member[0] if member else None
    if first_member:
        return first_member

    await ctx.send(f"{username} is not in the room.")
    raise Exception(f"User {username} not found in the room")

def check_and_rotate_if_time_to_timeout_decreased(timeout):
    global timeToTimeout
    if timeout < timeToTimeout:
        timeToTimeout = timeout
        rotation.append(rotation.pop(0))

bot.run(config["BOT_TOKEN"])