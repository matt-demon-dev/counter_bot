# counter_bot.py
# Counter-bot: Discord ping counter running on Railway

import os
import sqlite3
import discord
from discord.ext import commands
from aiohttp import web

# Load bot token from environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise RuntimeError('DISCORD_TOKEN environment variable not set')

# Database path
DB_PATH = 'pings.sqlite'

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        '''
        CREATE TABLE IF NOT EXISTS pings (
            user_id INTEGER PRIMARY KEY,
            count INTEGER NOT NULL DEFAULT 0
        )
        '''
    )
    conn.commit()
    conn.close()

# Minimal web server for Railway health checks
def create_web_app():
    app = web.Application()
    async def handle(request):
        return web.Response(text="Counter-bot is running.")
    app.add_routes([web.get('/', handle)])
    return app

# Subclass commands.Bot to start web server in setup_hook
class CounterBot(commands.Bot):
    async def setup_hook(self):
        # Start aiohttp server on assigned PORT
        app = create_web_app()
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv('PORT', 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"🌐 Web server running on port {port}")
        # Call parent setup_hook if needed
        await super().setup_hook()

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Instantiate bot
bot = CounterBot(command_prefix='!', description='Counter-bot: Tracks pings.', intents=intents)

@bot.event
async def on_ready():
    print(f'✔️ Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user in message.mentions:
        user_id = message.author.id
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT count FROM pings WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            count = row[0] + 1
            cursor.execute('UPDATE pings SET count = ? WHERE user_id = ?', (count, user_id))
        else:
            count = 1
            cursor.execute('INSERT INTO pings (user_id, count) VALUES (?, ?)', (user_id, count))
        conn.commit()
        conn.close()
        await message.channel.send(f'<@{user_id}> You have pinged Counter-bot {count} time{"s" if count != 1 else ""}!')

    # Ensure commands still work
    await bot.process_commands(message)

@bot.command(name='pings')
async def pings(ctx, member: discord.Member = None):
    target = member or ctx.author
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT count FROM pings WHERE user_id = ?', (target.id,))
    row = cursor.fetchone()
    conn.close()
    count = row[0] if row else 0
    await ctx.send(f'<@{target.id}> has pinged Counter-bot {count} time{"s" if count != 1 else ""}.')

if __name__ == '__main__':
    init_db()
    bot.run(DISCORD_TOKEN)
