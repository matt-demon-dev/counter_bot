# counter_bot.py
# Counter-bot: Discord ping counter (global count) running on Railway

import os
import sqlite3
import discord
from discord.ext import commands
from aiohttp import web

# Load bot token from environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise RuntimeError('DISCORD_TOKEN environment variable not set')

# Database path and initialization
db_path = 'counter.sqlite'

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # table for global counter (single row id=1)
    c.execute(
        '''
        CREATE TABLE IF NOT EXISTS counter (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            count INTEGER NOT NULL
        )
        '''
    )
    # ensure row exists
    c.execute('INSERT OR IGNORE INTO counter (id, count) VALUES (1, 0)')
    conn.commit()
    conn.close()

# Web app for Railway health checks
def create_app():
    app = web.Application()
    async def handle(request):
        return web.Response(text="Counter-bot is running.")
    app.add_routes([web.get('/', handle)])
    return app

# Custom Bot to start web server in setup_hook
class CounterBot(commands.Bot):
    async def setup_hook(self):
        # start web server
        app = create_app()
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.getenv('PORT', 8080))
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        print(f"🌐 Web server running on port {port}")
        await super().setup_hook()

# Define intents
token_intents = discord.Intents.default()
token_intents.message_content = True

# Instantiate bot
bot = CounterBot(command_prefix='!', description='Counter-bot: Tracks total pings.', intents=token_intents)

@bot.event
async def on_ready():
    print(f'✔️ Logged in as {bot.user} (ID: {bot.user.id})')

@bot.event
async def on_message(message):
    # ignore bots
t    if message.author.bot:
        return

    # if mentioned, increment global count\ n    if bot.user in message.mentions:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('UPDATE counter SET count = count + 1 WHERE id = 1')
        conn.commit()
        c.execute('SELECT count FROM counter WHERE id = 1')
        total = c.fetchone()[0]
        conn.close()
        await message.channel.send(f'🔔 Counter-bot has been pinged {total} time{"s" if total != 1 else ""}!')

    await bot.process_commands(message)

@bot.command(name='pings')
async def pings(ctx):
    """Show total pings to the bot."""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute('SELECT count FROM counter WHERE id = 1')
    total = c.fetchone()[0]
    conn.close()
    await ctx.send(f'🔔 Counter-bot has been pinged {total} time{"s" if total != 1 else ""}.')

if __name__ == '__main__':
    init_db()
    bot.run(DISCORD_TOKEN)
