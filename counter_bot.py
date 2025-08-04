# Discord bot that counts how many times it has been mentioned (pinged).
# The count is stored in an SQLite database to persist across restarts.

import sqlite3
import discord

# Set up intents to receive message content (required for mention detection):contentReference[oaicite:7]{index=7}.
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Initialize SQLite database and ensure a table exists to store the ping count.
db = sqlite3.connect('pings.sqlite')
cursor = db.cursor()
# Create a table with one row (id=1) to store the ping count.
cursor.execute('CREATE TABLE IF NOT EXISTS pings (id INTEGER PRIMARY KEY, count INTEGER)')
# Ensure there is a default row with id=1 if none exists.
cursor.execute('INSERT OR IGNORE INTO pings (id, count) VALUES (?, ?)', (1, 0))
db.commit()
db.close()

@client.event
async def on_ready():
    print(f'Logged in as {client.user} (ID: {client.user.id})')
    print('Ready to count mentions.')

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself to prevent feedback loops:contentReference[oaicite:8]{index=8}.
    if message.author == client.user:
        return

    # Check if the bot is mentioned in the message:contentReference[oaicite:9]{index=9}.
    if client.user in message.mentions:
        # Open a new database connection for this event.
        conn = sqlite3.connect('pings.sqlite')
        cursor = conn.cursor()
        # Get current ping count.
        cursor.execute('SELECT count FROM pings WHERE id = ?', (1,))
        row = cursor.fetchone()
        if row:
            count = row[0] + 1
            # Update the count in the database.
            cursor.execute('UPDATE pings SET count = ? WHERE id = ?', (count, 1))
        else:
            # If somehow the row is missing, create it.
            count = 1
            cursor.execute('INSERT INTO pings (id, count) VALUES (?, ?)', (1, count))
        conn.commit()
        conn.close()

        # Respond with the current total ping count.
        await message.channel.send(f'I have been mentioned {count} times so far!')

# Start the bot (replace 'YOUR_BOT_TOKEN' with your actual bot token).
client.run('MTQwMTY3NzA2NTkyOTA5NzIyNg.GTLKFe.JaM1taQ8hjLlupzGluVR993HEMnMZ5wUPSG-Vg')
