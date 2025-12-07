import os
import webbrowser
from datetime import datetime
from pathlib import Path

import git
import requests
from decouple import config
from langchain.tools import tool
from langchain_groq import ChatGroq
from tkinter import filedialog


api_key = config("API_KEY")
llm = ChatGroq(model="llama-3.3-70b-versatile", api_key=api_key)


@tool
def temperaturas(cidade: str) -> str:
    """Retorna APENAS A TEMPERATURA atual da cidade informada."""
    try:
        api_clima = config("API_CLIMA")
        site = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_clima}&lang=pt_br"

        requisicao = requests.get(site)
        requisicao_dicionario = requisicao.json()
        temperatura = requisicao_dicionario["main"]["temp"] - 273.15
    except (requests.ConnectionError, requests.HTTPError):
        return "Erro ao conectar com o serviço de clima."
    else:
        return f"{temperatura:.1f}"


@tool
def pesquisar(assunto: str) -> str:
    """Abre o navegador com os resultados da pesquisa do termo informado."""
    try:
        url = f"https://www.google.com/search?q={assunto}"
        webbrowser.open(url)
        return "Pesquisa realizada com sucesso."
    except Exception as e:
        print(f"[Erro ao pesquisar]: {e}")
        return f"Erro ao pesquisar: {e}"


@tool
def hora_atual() -> str:
    """Retorna a hora atual."""
    return datetime.now().strftime("%H:%M")


@tool
def data_atual() -> str:
    """Retorna a data atual."""
    return str(datetime.now().strftime("%d/%m/%Y"))


@tool
def buscar_cotacoes(cotacao: str) -> str:
    """Retorna a cotação da moeda informada. Porém você deve informar a sigla da moeda, por exemplo: usd, eur, btc, etc."""
    url = f"https://economia.awesomeapi.com.br/last/{cotacao}"
    r = requests.get(url)

    if r.status_code == 200:
        dados = r.json()
        resultado = dados[cotacao.upper() + "BRL"]["bid"]
        resultado = float(resultado)
        return f"R$ {resultado:.2f}"
    else:
        return "Erro ao buscar cotação."


@tool
def abrir_apps(app: str) -> str:
    """Abre o aplicativo informado lembrando sempre que estamos no Linux."""
    try:
        os.system(f"{app}")
        return f"Aplicativo {app} aberto com sucesso."
    except Exception as e:
        print(f"[Erro ao abrir aplicativo]: {e}")
        return f"Erro ao abrir aplicativo: {e}"


def sugerir_commit():
    try:
        repositorio = filedialog.askdirectory(title="Selecione o repositório Git")
        if not repositorio:
            return "Nenhum repositório selecionado."
        CAMINHO_REPO = Path(repositorio)
    except Exception:
        return "Erro ao acessar o repositório."

    try:
        repo = git.Repo(CAMINHO_REPO)
        diff = repo.git.diff("--cached")
        if not diff:
            return "Nenhuma mudança encontrada."
        return diff
    except Exception:
        return "Erro ao obter diff."



def gerar_descricao_llm(diff_texto: str) -> str:
    """Gera uma descrição clara e concisa das alterações feitas no código."""
    prompt = f"""
    Explique claramente o que foi alterado neste diff de código. Seja conciso e responda em português.

    Diff: {diff_texto}
    """

    try:
        resposta = llm.invoke(prompt)
        return (
            resposta.strip() if isinstance(resposta, str) else resposta.content.strip()
        )
    except Exception as e:
        print(f"[Erro ao chamar o modelo]: {e}")
        return "Não foi possível gerar descrição."


def classificar_mudanca(descricao: str) -> str:
    """Classifica a descrição das alterações feitas no código com uma tag de commit semântico."""
    prompt = f"""
    Classifique a seguinte descrição com uma tag de commit semântico.

    Tags possíveis:
    - feat
    - fix
    - refactor
    - docs
    - test
    - chore

    Descrição:
    \"\"\"{descricao}\"\"\"

    Responda apenas com a tag correta.
    """
    try:
        resposta = llm.invoke(prompt)
        if hasattr(resposta, "content"):
            resposta = resposta.content
        tag = resposta.strip().lower()
        if tag in ["feat", "fix", "refactor", "docs", "test", "chore"]:
            return tag
        return "chore"
    except Exception as e:
        print(f"[Erro ao classificar]: {e}")
        return "chore"


@tool
def gerar_mensagem_commit() -> str:
    """Gere uma mensagem de commit semântico com base nas alterações staged, SEMPRE no formato 'tipo: descrição'.
    Exemplo: 'feat: Adiciona nova funcionalidade X'. Quero que a descrição seja clara e concisa, e que o tipo do commit seja classificado corretamente.
    OBS: Ignore as as mudanças em arquivos de audio, vídeo, imagem e outros arquivos binários.
    SEMPRE RETORNE A MENSAGEM EM APENAS UMA LINHA NO FORMATO CORRETO.
    """
    diff = sugerir_commit()  # pega o diff atual
    descricao = gerar_descricao_llm(diff)

    if "Não foi possível gerar" in descricao:
        return "chore: Atualizações no código"

    tipo = classificar_mudanca(descricao)
    return f"{tipo}: {descricao}"
