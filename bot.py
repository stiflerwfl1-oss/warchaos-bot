import discord
from discord.ext import commands
import aiohttp
import re
import json
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_JS_URL = "https://stiflerwfl1-oss.github.io/Conquistas-Warface/data.js"

@bot.event
async def on_ready():
    print(f'WarChaos Bot conectado como {bot.user.name}!')

@bot.command(aliases=['conquistas', 'fita', 'fitas', 'marca', 'insignia'])
async def conquista(ctx, *, nome_busca: str):
    mensagem_status = await ctx.send("Consultando o banco de dados do WarChaos...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_JS_URL) as response:
                if response.status != 200:
                    await mensagem_status.edit(content="Erro ao acessar o site WarChaos.")
                    return

                js_content = await response.text()

                # Extrai o array do JS usando regex nao-greedy
                match = re.search(r'const achievementsData\s*=\s*(\[.*?\])\s*;', js_content, re.DOTALL)
                if not match:
                    match = re.search(r'const achievementsData\s*=\s*(\[.*?\])', js_content, re.DOTALL)
                if not match:
                    await mensagem_status.edit(content="Erro ao ler a base de dados.")
                    return

                json_string = match.group(1)
                dados_conquistas = json.loads(json_string)

                # Coleta TODOS os resultados que contem o nome buscado
                resultados = [
                    item for item in dados_conquistas
                    if nome_busca.lower() in item.get('name', '').lower()
                ]

                if not resultados:
                    await mensagem_status.edit(content=f"Nenhuma conquista encontrada com o nome '{nome_busca}'.")
                    return

                await mensagem_status.edit(content=f"Encontrada(s) **{len(resultados)}** conquista(s) para '{nome_busca}':")

                for resultado in resultados:
                    img_url = resultado.get('image', '')
                    if not img_url:
                        img_url = resultado.get('fallbackOriginalUrl', '')

                    embed = discord.Embed(
                        title=f"{resultado['name']}",
                        description=resultado.get('description', 'Sem descricao'),
                        color=0xDC143C
                    )
                    embed.add_field(name="Objetivo", value=str(resultado.get('objective', 'N/A')), inline=True)
                    embed.add_field(name="Tipo", value=str(resultado.get('type', 'Desconhecido')).title(), inline=True)
                    tags = resultado.get('tags', [])
                    if tags:
                        embed.add_field(name="Tags", value=', '.join(tags), inline=True)
                    if img_url:
                        embed.set_image(url=img_url)
                    embed.set_footer(text="Fonte: WarChaos Catalog")

                    await ctx.send(embed=embed)

    except Exception as e:
        await mensagem_status.edit(content=f"Ocorreu um erro ao processar os dados: {e}")

bot.run(os.environ.get('DISCORD_TOKEN'))
