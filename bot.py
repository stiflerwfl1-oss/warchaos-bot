import discord
from discord.ext import commands
import aiohttp
import re
import json

# Configuração do bot com o prefixo "!"
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# A URL do seu arquivo JS direto do GitHub Pages
DATA_JS_URL = "https://stiflerwfl1-oss.github.io/Conquistas-Warface/data.js"

@bot.event
async def on_ready():
    print(f'WarChaos Bot conectado como {bot.user.name}!')

@bot.command()
async def conquista(ctx, *, nome_busca: str):
    mensagem_status = await ctx.send("🔍 Consultando o banco de dados do WarChaos...")
    
    try:
        # Baixa o arquivo data.js
        async with aiohttp.ClientSession() as session:
            async with session.get(DATA_JS_URL) as response:
                if response.status != 200:
                    await mensagem_status.edit(content="❌ Erro ao acessar o site WarChaos.")
                    return
                js_content = await response.text()
        
        # Como o seu data.js tem um array 'const achievementsData = [ ... ];'
        # Usamos Regex para capturar tudo que está dentro dos colchetes principais
        match = re.search(r'const achievementsData = (\[.*?\]);', js_content, re.DOTALL)
        
        if not match:
            await mensagem_status.edit(content="❌ Erro ao ler a base de dados.")
            return
            
        json_string = match.group(1)
        
        # O data.js usa chaves sem aspas (ex: id: "localach0"), o que quebra o parser JSON padrão do Python
        # Essa rotina limpa as chaves para transformar num JSON válido
        json_string = re.sub(r'(\w+):', r'"\1":', json_string)
        # Remove aspas simples e troca por duplas para garantir
        json_string = json_string.replace("'", '"')
        
        # Carrega os dados em um dicionário Python
        dados_conquistas = json.loads(json_string)
        
        # Faz a busca (Ignorando letras maiúsculas e minúsculas)
        resultado = None
        for item in dados_conquistas:
            if nome_busca.lower() in item['name'].lower():
                resultado = item
                break
                
        if resultado:
            # Pega a URL da imagem. Se a imagem for um caminho local (começando com '.'), 
            # ele concatena com a URL raiz do seu site
            img_url = resultado['image']
            if img_url.startswith('.'):
                img_url = img_url.replace('.', 'https://stiflerwfl1-oss.github.io/Conquistas-Warface', 1)
                
            embed = discord.Embed(
                title=f"🏆 {resultado['name']}",
                description=resultado['description'],
                color=0xDC143C # Vermelho, combinando com o Warface
            )
            embed.add_field(name="Objetivo", value=str(resultado.get('objective', 'N/A')), inline=True)
            embed.add_field(name="Tipo", value=resultado.get('type', 'Desconhecido').title(), inline=True)
            
            tags = resultado.get('tags', '')
            if tags:
                embed.add_field(name="Tags", value=tags, inline=True)
                
            embed.set_thumbnail(url=img_url)
            embed.set_footer(text="Fonte: WarChaos Catalog")
            
            await mensagem_status.delete()
            await ctx.send(embed=embed)
        else:
            await mensagem_status.edit(content=f"❌ Nenhuma conquista encontrada com o nome **'{nome_busca}'**.")
            
    except Exception as e:
        await mensagem_status.edit(content=f"❌ Ocorreu um erro ao processar os dados: {e}")

import os
bot.run(os.environ.get('DISCORD_TOKEN'))