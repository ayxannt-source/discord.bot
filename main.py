import os
import io
import discord
from discord.ext import commands
from discord.ui import View, Select, Button

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Ayarların tutulacağı sözlük
ticket_settings = {}

# --- TICKET KAPATMA VE TRANSCRIPT BÖLÜMÜ ---
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🔒 Ticket'ı Kapat", style=discord.ButtonStyle.red, custom_id="close_ticket_btn")
    async def close_ticket(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message("Ticket kapatılıyor ve transcript hazırlanıyor...", ephemeral=True)
        
        channel = interaction.channel
        guild = interaction.guild
        
        # Sohbet Geçmişini Çekme (Transcript)
        messages = []
        async for msg in channel.history(limit=500, oldest_first=True):
            time_str = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            messages.append(f"[{time_str}] {msg.author} ({msg.author.id}): {msg.content}")
        
        transcript_text = "\n".join(messages)
        file_bytes = io.BytesIO(transcript_text.encode("utf-8"))
        transcript_file = discord.File(file_bytes, filename=f"transcript-{channel.name}.txt")

        # Transcript Kanalını Bulma ve Gönderme
        settings = ticket_settings.get(guild.id, {})
        transcript_channel_id = settings.get("transcript_channel_id")
        
        if transcript_channel_id:
            transcript_chan = guild.get_channel(transcript_channel_id)
            if transcript_chan:
                embed = discord.Embed(
                    title="📜 Ticket Transcript Kaydı",
                    description=f"**Kanal:** {channel.name}\n**Kapatan:** {interaction.user.mention}",
                    color=discord.Color.gold()
                )
                await transcript_chan.send(embed=embed, file=transcript_file)

        await channel.send("Kanal 5 saniye içinde siliniyor...")
        import asyncio
        await asyncio.sleep(5)
        await channel.delete()

# --- TICKET AÇMA PANELİ (KATEGORİLİ) ---
class TicketCategorySelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Kamp Şikayet", emoji="🏕️", description="Kamp ile ilgili şikayet talebi"),
            discord.SelectOption(label="İo Şikayet", emoji="⚠️", description="İo ile ilgili şikayet talebi"),
            discord.SelectOption(label="İo Yetkili Başvuru", emoji="📝", description="İo yetkili alım başvurusu")
        ]
        super().__init__(placeholder="Açmak istediğiniz ticket kategorisini seçin...", options=options, custom_id="ticket_category_select")

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        member = interaction.user
        category_name = self.values[0]

        settings = ticket_settings.get(guild.id, {})
        category_id = settings.get("category_id")
        staff_role_id = settings.get("staff_role_id")

        category = guild.get_channel(category_id) if category_id else None
        staff_role = guild.get_role(staff_role_id) if staff_role_id else None

        # İzinler (Açan kişi, Bot ve Yetkili Rolü görebilir)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if staff_role:
            overwrites[staff_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        clean_cat_name = category_name.lower().replace(" ", "-")
        ticket_channel = await guild.create_text_channel(
            name=f"{clean_cat_name}-{member.name}",
            category=category,
            overwrites=overwrites
        )

        embed = discord.Embed(
            title=f"🎫 {category_name} Talebi",
            description=f"Merhaba {member.mention}, **{category_name}** konusu için destek talebiniz oluşturuldu.\nYetkililer en kısa sürede ilgilenecektir.",
            color=discord.Color.green()
        )
        await ticket_channel.send(content=f"{member.mention} {staff_role.mention if staff_role else ''}", embed=embed, view=CloseTicketView())
        await interaction.response.send_message(f"Ticket kanalınız oluşturuldu: {ticket_channel.mention}", ephemeral=True)

class TicketPublicView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

# --- KURULUM SİHİRBAZI (!ticket-kur) ---
class SetupView(View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.selected_role = None
        self.selected_category = None
        self.selected_transcript = None

        # Rol Seçimi
        role_options = [discord.SelectOption(label=r.name, value=str(r.id)) for r in ctx.guild.roles if not r.is_default()][:25]
        if role_options:
            role_select = Select(placeholder="1. Yetkili Rolünü Seçin", options=role_options)
            role_select.callback = self.role_callback
            self.add_item(role_select)

        # Kategori Seçimi
        cat_options = [discord.SelectOption(label=c.name, value=str(c.id)) for c in ctx.guild.categories][:25]
        if cat_options:
            cat_select = Select(placeholder="2. Ticket Kategorisini Seçin", options=cat_options)
            cat_select.callback = self.cat_callback
            self.add_item(cat_select)

        # Transcript Kanalı Seçimi
        text_options = [discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in ctx.guild.text_channels][:25]
        if text_options:
            trans_select = Select(placeholder="3. Transcript Kanalını Seçin", options=text_options)
            trans_select.callback = self.trans_callback
            self.add_item(trans_select)

    async def role_callback(self, interaction: discord.Interaction):
        self.selected_role = int(interaction.data['values'][0])
        await interaction.response.send_message("Yetkili rolü seçildi!", ephemeral=True)

    async def cat_callback(self, interaction: discord.Interaction):
        self.selected_category = int(interaction.data['values'][0])
        await interaction.response.send_message("Kategori seçildi!", ephemeral=True)

    async def trans_callback(self, interaction: discord.Interaction):
        self.selected_transcript = int(interaction.data['values'][0])
        await interaction.response.send_message("Transcript kanalı seçildi!", ephemeral=True)

    @discord.ui.button(label="Kurulumu Tamamla ve Paneli Gönder", style=discord.ButtonStyle.green, row=4)
    async def finish_setup(self, interaction: discord.Interaction, button: Button):
        if not (self.selected_role and self.selected_category and self.selected_transcript):
            await interaction.response.send_message("Lütfen tüm seçimleri (Rol, Kategori, Transcript) yapın!", ephemeral=True)
            return

        ticket_settings[interaction.guild.id] = {
            "staff_role_id": self.selected_role,
            "category_id": self.selected_category,
            "transcript_channel_id": self.selected_transcript
        }

        embed = discord.Embed(
            title="🎫 Destek Merkezi",
            description="Aşağıdaki menüden ihtiyacınız olan destek konusunu seçerek ticket açabilirsiniz.",
            color=discord.Color.blue()
        )
        await interaction.channel.send(embed=embed, view=TicketPublicView())
        await interaction.response.send_message("Ticket paneli başarıyla kuruldu!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"{bot.user} aktif ve Ticket Sistemi Hazır!")

@bot.command(name="ticket-kur")
@commands.has_permissions(administrator=True)
async def ticket_kur(ctx):
    embed = discord.Embed(
        title="⚙️ Ticket Sistemi Kurulumu",
        description="Lütfen aşağıdaki menülerden sırasıyla Yetkili Rolünü, Ticketların açılacağı Kategoriyi ve Transcriptlerin gideceği Kanalı seçip en alttaki butona tıklayın.",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed, view=SetupView(ctx))

bot.run(os.getenv("DISCORD_TOKEN"))
