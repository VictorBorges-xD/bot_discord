import discord


def criar_embed_produto(nome, preco, estoque, url):
    if preco is None:
        preco_texto = "Indisponível"
    else:
        preco_texto = f"R$ {preco:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    estoque_texto = "✅ Em estoque" if estoque else "❌ Esgotado"

    cor = discord.Color.green() if estoque else discord.Color.red()

    embed = discord.Embed(
        title=nome,
        url=url,
        color=cor
    )

    embed.add_field(name="Preço", value=preco_texto, inline=True)
    embed.add_field(name="Estoque", value=estoque_texto, inline=True)

    embed.set_footer(text="Monitoramento Kabum")

    return embed
