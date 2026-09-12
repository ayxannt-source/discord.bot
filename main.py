import os
import discord
from discord.ext import commands
from discord.ui import Button, View

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ticket Kapatma Butonu
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Bilet kapatılıyor, bu kanal 5 saniye içinde silinecektir...")
        import asyncio
        await asyncio.sleep(5)
        await interaction.channel.delete()

# Ticket Açma Butonu
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ticket Aç", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: Button):
        guild = interaction.guild
        member = interaction.user

        # Kullanıcının zaten açık ticket'ı var mı kontrol et
        existing_channel = discord.utils.get(guild.channels, name=f"ticket-{member.name.lower()}")
        if existing_channel:
            await interaction.response.send_message(f"Zaten açık bir ticket'ınız var: {existing_channel.mention}", ephemeral=True)
            return

        # Kanal izinlerini ayarla (Sadece ticket açan ve bot görebilsin)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }

        # Ticket kanalını oluştur
        channel = await guild.create_text_channel(name=f"ticket-{member.name}", overwrites=overwrites)
        
        await channel.send(f"Merhaba {member.mention}, nasıl yardımcı olabiliriz?", view=CloseTicketView())
        await interaction.response.send_message(f"Ticket kanalınız oluşturuldu: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user} olarak giriş yapıldı ve Ticket sistemi aktif!")

# Ticket Paneli Kurma Komutu (!ticket-kur)
@bot.command()
@commands.has_permissions(administrator=True)
async def ticket_kur(ctx):
    embed = discord.Embed(
        title="🎫 Destek Talebi",
        description="Destek ekibimizle görüşmek için aşağıdaki butona tıklayarak ticket açabilirsiniz.",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed, view=TicketView())

bot.run(os.getenv("DISCORD_TOKEN"))
