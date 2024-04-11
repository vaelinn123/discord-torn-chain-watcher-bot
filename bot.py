import requests
import discord
import json
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

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

@bot.command(name="rotation-clear", description="Clears the rotation.")
async def clear_rotation(ctx):
    print("Clearing rotation")
    global rotation
    rotation = []
    await ctx.send(content="Rotation cleared")

@bot.command(name="rotation-info", description="Prints chain information.")
async def rotation_info(ctx):
    print("rotation : ", rotation)
    rotation_usernames = [f"{i+1}. {member.name}" for i, member in enumerate(rotation)]
    rotation_str = '\n'.join(rotation_usernames)
    await ctx.send(content=f'```Current rotation:\n{rotation_str}```')

@bot.command(name="chain-timer", description="Prints chain information.")
async def get_faction_chain_timer(ctx):
    print("Checking chain timer")
    url = f'https://api.torn.com/faction/?selections=chain&key={config["TORN_API_KEY"]}'
    print("URL : ", url)
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
    
@bot.command(name="rotation-remove", description="Removes a user from the rotation.")
async def handle_rotation_remove(ctx):
    try:
        user = await get_and_validate_member(ctx)
        await remove_user_from_rotation(user, ctx)
        await rotation_info(ctx)
    except Exception as error:
        print(f"Error fetching user: {error}")
        return

@bot.command(name="chain-start", description="Starts the chain.")
async def handle_chain_start(ctx):
    chain_task.start(ctx)

@bot.command(name="chain-stop", description="Stops the chain.")
async def handle_chain_stop(ctx):
    chain_task.cancel()
    await ctx.send(content=f'Timer stopped, use !chain-start to start again.')

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
    print("Removing user from rotation", user)
    rotation.remove(user)

async def add_user_to_rotation(user, ctx):
    if user in rotation:
        await ctx.send(f'{user.name} is already in the rotation.')
        return
    print("Adding user to rotation", user)
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