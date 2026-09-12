import os
from flask import Flask
from threading import Thread
import discord
from discord.ext import commands

# 1. Web Server (Render'ın kapanmaması için)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# 2. Discord Bot Tanımlaması (Önce 'bot' değişkeni oluşturulmalı)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# 3. Bot Eventleri
@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı!")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    icerik = message.content.lower().strip()

    if icerik == "sa" or icerik.startswith("selam"):
        await message.channel.send("Aleyküm Selam")

    await bot.process_commands(message)

# 4. Çalıştırma
if __name__ == "__main__":
    Thread(target=run_web).start()
    
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.run(token)
    else:
        print("HATA: DISCORD_TOKEN değişkeni bulunamadı!")
