import discord
from discord.ext import commands
from discord.ext import tasks
import google.generativeai as genai
import textwrap
import os
from dotenv import load_dotenv
from kabum_promos import cadastrar_produto, carregar_dados, salvar_dados, atualizar_produto
from embeds import criar_embed_produto
from datetime import time
import asyncio


load_dotenv()
api_key = os.getenv("api_key")
discord_token = os.getenv("discord_token")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemma-3-27b-it")

permissoes = discord.Intents.all() #garante ao bot todas as permissoes do discord
bot = commands.Bot('.', intents = permissoes, help_command=None)

def url_valida(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

@bot.event
async def on_ready():
    if not loop_diario.is_running():
        loop_diario.start()
    print("loop diário pronto.")
    print(f"sucesso com {bot.user.display_name}")


@bot.command(help = "Testa se o bot ta online")
async def ping(ctx:commands.Context):
    await ctx.send("pong!")


@bot.command(help = "lista todos os comandos")
async def ajuda(ctx:commands.Context):
    comandos = bot.commands #todos comandos selecionados aqui
    await ctx.send("comandos disponiveis: \n")
    lista_comandos = []
    for comando in comandos:
        lista_comandos.append(comando.name+ " - " +comando.help)
        
    resposta = "\n".join(lista_comandos)
    await ctx.send(resposta)


@bot.command(help= "mostra as informaçoes do servidor")
async def servinf(ctx:commands.Context):
    serv = ctx.guild
    servidor = (
        f"nome = {serv.name}\n"
        f"idserv = {serv.id}\n"
        f"dono = {serv.owner}\n"
        f"membros = {serv.member_count}\n"
        f"criado em = {serv.created_at.strftime("%d/%m/%Y")}")

    await ctx.send(servidor)


lista_mensagens = []
@bot.command(help="conversar com o chat")
async def chat(ctx: commands.Context, *, quest):
    personalidade = (
        "Você é um assistente agressivo, sarcástico e mal-educado. "
        "Se o usuário te xingar, você DEVE xingar de volta. "
        "Não seja educado, não seja amigável.\n\n"
    )

    mensagem = personalidade + quest

    lista_mensagens.append({
        "role": "user",
        "parts": [mensagem]
    })

    resposta = model.generate_content(lista_mensagens)

    lista_mensagens.append({
        "role": "model",
        "parts": [resposta.text]
    })

    for parte in textwrap.wrap(resposta.text, width=2000):
        await ctx.reply(parte)


@bot.command(help="adiciona um produto para monitoramento de preço")
async def add_p(ctx, url: str):

    if not url_valida(url):
        await ctx.send("❌ URL inválida. Certifique-se de que começa com http:// ou https://")
        return
    if "kabum.com.br/produto/" not in url:
        await ctx.send("❌ Esse comando aceita apenas links de produtos da Kabum.")
        return


    produto = cadastrar_produto(url)

    if produto is None:
        await ctx.send("❌ Não consegui cadastrar esse produto.")
        return
    
    dados = carregar_dados()
    produtos = dados["produtos"]
    user_id = ctx.author.id

    if user_id not in produto["monitorando"]:
        produtos[url]["monitorando"].append(user_id)
        salvar_dados(dados)
        await ctx.send("✅ Produto cadastrado e você foi adicionado ao monitoramento.")
    else:
        await ctx.send("ℹ️ Você já está monitorando esse produto.")


@bot.command(help="Ativa o loop diário de verificação de preços")
async def a_loop(ctx):
    dados = carregar_dados()
    dados["canal_loop"] = ctx.channel.id
    salvar_dados(dados)

    await ctx.send("✅ Loop diário ativado neste canal (06:00 da manhã).")


@bot.command(help="Desativa o loop diário de verificação de preços")
async def s_loop(ctx):
    dados = carregar_dados()

    if "canal_loop" in dados:
        del dados["canal_loop"]
        salvar_dados(dados)
        await ctx.send("⛔ Loop diário desativado.")
    else:
        await ctx.send("ℹ️ Nenhum loop ativo no momento.")


@tasks.loop(time=time(hour=9, minute=0))
async def loop_diario():
    dados = carregar_dados()

    canal_id = dados.get("canal_loop")
    if not canal_id:
        return

    canal = bot.get_channel(canal_id)
    if not canal:
        return

    for url, produto in dados["produtos"].items():
        preco_antigo = produto["preco"]
        dados_sites = atualizar_produto(url)
        if not dados_sites:
            continue

        preco_novo = dados_sites["preco"]

        produto["preco"] = preco_novo
        produto["estoque"] = dados_sites["estoque"]
        produto["nome"] = dados_sites["nome"]

        embed = criar_embed_produto(produto["nome"], preco_novo, produto["estoque"], url)

        mensagem = None

        if preco_antigo and preco_novo and preco_novo < preco_antigo:
            mentions = " ".join(f"<@{uid}>" for uid in produto["monitorando"])
            mensagem = f"🔥 **PREÇO BAIXOU!** {mentions}"

        await canal.send(content=mensagem, embed=embed)
        await asyncio.sleep(2)

    salvar_dados(dados)


bot.run(discord_token)