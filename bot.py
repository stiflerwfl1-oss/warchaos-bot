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

# Mapa de tipos canonicos (igual ao app.js do site)
TYPE_MAP = {
    'mark': 'marca', 'badge': 'insignia', 'stripe': 'fita',
    'marca': 'marca', 'insignia': 'insignia', 'insiginia': 'insignia', 'fita': 'fita',
}

def get_canonical_type(type_raw):
    return TYPE_MAP.get(str(type_raw or '').strip().lower(), str(type_raw or '').lower())

def get_type_label(type_raw):
    labels = {'marca': 'Marca', 'insignia': 'Insignia', 'fita': 'Fita'}
    return labels.get(get_canonical_type(type_raw), 'Conquista')

def get_img_url(item):
    url = item.get('image') or item.get('fallbackOriginalUrl') or ''
    # Garante que a URL e valida antes de usar
    if url and url.startswith('http'):
        return url
    return ''

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

                # Captura APENAS o array achievementsData, que termina com ];
                # O arquivo tem dois arrays; pegamos somente o primeiro
                match = re.search(
                    r'const\s+achievementsData\s*=\s*(\[.*?\])\s*;',
                    js_content,
                    re.DOTALL
                )
                if not match:
                    await mensagem_status.edit(content="Erro ao ler a base de dados.")
                    return

                dados_conquistas = json.loads(match.group(1))

                # Busca APENAS pelo nome da conquista
                q = nome_busca.lower()
                resultados = [
                    item for item in dados_conquistas
                    if q in item.get('name', '').lower()
                ]

                if not resultados:
                    await mensagem_status.edit(content=f"Nenhuma conquista encontrada para '{nome_busca}'.")
                    return

                await mensagem_status.edit(content=f"Encontrada(s) **{len(resultados)}** conquista(s) para '{nome_busca}':")

                for resultado in resultados:
                    img_url = get_img_url(resultado)
                    tipo_label = get_type_label(resultado.get('type', ''))

                    # Cor por tipo
                    cores = {'Marca': 0xa78bfa, 'Insignia': 0x60a5fa, 'Fita': 0x34d399}
                    cor = cores.get(tipo_label, 0xDC143C)

                    embed = discord.Embed(
                        title=resultado.get('name', 'Sem nome'),
                        description=resultado.get('description', 'Sem descricao'),
                        color=cor
                    )

                    # Campos obrigatorios
                    objective = resultado.get('objective') or resultado.get('goal') or resultado.get('eliminations')
                    if objective is not None:
                        embed.add_field(name="Objetivo", value=str(objective), inline=True)

                    embed.add_field(name="Tipo", value=tipo_label, inline=True)

                    # Campos opcionais do site
                    if resultado.get('weapon'):
                        embed.add_field(name="Arma", value=resultado['weapon'], inline=True)
                    if resultado.get('mode'):
                        embed.add_field(name="Modo", value=resultado['mode'], inline=True)
                    if resultado.get('operationRaw'):
                        embed.add_field(name="Operacao", value=resultado['operationRaw'], inline=True)
                    if resultado.get('mapRaw') or resultado.get('map'):
                        embed.add_field(name="Mapa", value=resultado.get('mapRaw') or resultado.get('map'), inline=True)

                    tags = resultado.get('tags', [])
                    if tags:
                        embed.add_field(name="Tags", value=', '.join(tags), inline=True)

                    # Gold indicator
                    is_gold = bool(resultado.get('isGold')) or 'Gold' in resultado.get('tags', [])
                    is_gold_ribbon = (
                        get_canonical_type(resultado.get('type', '')) == 'fita' and
                        'dourada' in resultado.get('name', '').lower() and
                        str(objective) == '999'
                    )
                    if is_gold or is_gold_ribbon:
                        embed.add_field(name="Categoria", value="Star Fita Gold" if is_gold_ribbon else "Star Arma Gold", inline=True)

                    if img_url:
                        embed.set_image(url=img_url)

                    embed.set_footer(text=f"Fonte: WarChaos Catalog | ID: {resultado.get('id', 'N/A')}")

                    await ctx.send(embed=embed)

    except Exception as e:
        await mensagem_status.edit(content=f"Ocorreu um erro ao processar os dados: {e}")

bot.run(os.environ.get('DISCORD_TOKEN'))
