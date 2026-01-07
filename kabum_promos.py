import requests
from bs4 import BeautifulSoup
import json
import os

ARQUIVO_DADOS = "dados_kabum.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def salvar_dados(dados):
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def atualizar_produto(url):
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "html.parser")

    h1 = soup.find("h1")
    if not h1:
        return None

    nome = h1.get_text().strip()

    texto = soup.get_text().lower()
    em_estoque = "esgotado" not in texto

    preco = None
    if em_estoque:
        h4 = soup.find("h4", class_="text-4xl")
        if h4:
            preco = float(
                h4.get_text()
                .replace("R$", "")
                .replace(".", "")
                .replace(",", ".")
                .strip()
            )

    return {
        "nome": nome,
        "preco": preco,
        "estoque": em_estoque
    }

def cadastrar_produto(url):
    dados_site = atualizar_produto(url)
    if dados_site is None:
        return None

    dados = carregar_dados()

    if "produtos" not in dados:
        dados["produtos"] = {}

    # se ainda não existe
    if url not in dados["produtos"]:
        dados["produtos"][url] = {
            "nome": dados_site["nome"],
            "preco": dados_site["preco"],
            "estoque": dados_site["estoque"],
            "monitorando": []
        }
    else:
        # só atualiza dados do produto
        dados["produtos"][url]["nome"] = dados_site["nome"]
        dados["produtos"][url]["preco"] = dados_site["preco"]
        dados["produtos"][url]["estoque"] = dados_site["estoque"]

    salvar_dados(dados)
    return dados["produtos"][url]

