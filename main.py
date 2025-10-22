import discord
from discord.ext import commands
import google.generativeai as genai
import textwrap
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("gem_KEY")
discord_token = os.getenv("DISCORD_TOKEN")

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

permissoes = discord.Intents.all() #garante ao bot todas as permissoes do discord
bot = commands.Bot('.', intents = permissoes, help_command=None)

@bot.event
async def on_ready():
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
        f"mebros = {serv.member_count}\n"
        f"criado em = {serv.created_at.strftime("%d/%m/%Y")}")

    await ctx.send(servidor)

lista_mensagens = []
@bot.command(help="conversar com o chat")
async def chat(ctx:commands.Context, *, quest):
    lista_mensagens.append({"role": "user", "parts": [quest]})
    resposta = model.generate_content(lista_mensagens)
    lista_mensagens.append({"role": "model", "parts": [resposta.text]})
    for parte in textwrap.wrap(resposta.text, width=2000):
        await ctx.reply(parte)

bot.run(discord_token)