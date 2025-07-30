import os
import webbrowser
from datetime import datetime
from pathlib import Path

import git
import requests
from decouple import config
from langchain.agents import tool
from langchain_groq import ChatGroq


api_key = config("API_KEY")
llm = ChatGroq(model="llama3-70b-8192", api_key=api_key)


@tool
def temperaturas(cidade: str) -> str:
    """Retorna APENAS A TEMPERATURA atual da cidade informada."""
    try:
        api_key = config("API_KEY_CLIMA")
        site = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&lang=pt_br"

        requisicao = requests.get(site)
        requisicao_dicionario = requisicao.json()
        temperatura = requisicao_dicionario["main"]["temp"] - 273.15
    except (requests.ConnectionError, requests.HTTPError):
        return 0
    else:
        return f"{temperatura:.1f}"


@tool
def ver_videos(video: str) -> None:
    """Abre o navegador com os vídeos relacionados ao termo pesquisado."""
    videos = f"https://www.youtube.com/results?search_query={video}"
    webbrowser.open(videos)


@tool
def pesquisar(assunto: str) -> None:
    """Abre o navegador com os resultados da pesquisa do termo informado."""
    url = f"https://www.google.com/search?q={assunto}"
    webbrowser.open(url)


@tool
def hora_atual() -> str:
    """Retorna a hora atual."""
    return datetime.now().strftime("%H:%M")


@tool
def data_atual() -> str:
    """Retorna a data atual."""
    return datetime.now().strftime("%d/%m/%Y")


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
def abrir_apps(app: str) -> None:
    """Abre o aplicativo informado lembrando sempre que estamos no Linux."""
    os.system(f"{app}")


def sugerir_commit():
    """Sugere um commit baseado nas alterações feitas no repositório."""
    CAMINHO_REPO = Path(
        "/home/mariva/Documentos/projetos/assistente_virtual"
    )  # Ex: Path("/home/mariva/Documentos/meu_projeto")

    # Abrir repositório
    repo = git.Repo(CAMINHO_REPO)
    diff = repo.git.diff("--cached")  # apenas os arquivos adicionados com `git add`

    return diff


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
    """Gera uma mensagem de commit semântico com base nas alterações staged, SEMPRE especificando o TIṔO do commit.
    SEMPRE mostre a mensagem de commit pulando duas linhas depois do contexto das mudanças.
    OBS: Ignore as as mudanças em arquivos de audio, vídeo, imagem e outros arquivos binários.
    """
    diff = sugerir_commit()  # pega o diff atual
    descricao = gerar_descricao_llm(diff)

    if "Não foi possível gerar" in descricao:
        return "chore: Atualizações no código"

    tipo = classificar_mudanca(descricao)
    return f"{tipo}: {descricao}"
