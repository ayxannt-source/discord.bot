@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Mesajı küçük harfe çevirip başındaki ve sonundaki boşlukları temizleyin
    icerik = message.content.lower().strip()

    # Yalnızca "sa" yazıldıysa VEYA mesaj "selam" ile başlıyorsa yanıt ver
    if icerik == "sa" or icerik.startswith("selam"):
        await message.channel.send("Aleyküm Selam")

    await bot.process_commands(message)
