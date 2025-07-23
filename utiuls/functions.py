import requests
import webbrowser
from langchain.agents import tool
from decouple import config
from datetime import datetime
import os


@tool
def temperaturas(cidade: str) -> str:
        '''Retorna APENAS A TEMPERATURA atual da cidade informada.'''
        try:
            api_key = config("API_KEY_CLIMA")
            site = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&lang=pt_br"

            requisicao = requests.get(site)
            requisicao_dicionario = requisicao.json()
            temperatura = requisicao_dicionario['main']['temp'] - 273.15
        except (requests.ConnectionError, requests.HTTPError):
            return 0
        else:
            return f'{temperatura:.1f}'
        

@tool
def ver_videos(video: str) -> None:
    '''Abre o navegador com os vídeos relacionados ao termo pesquisado.'''
    videos = f'https://www.youtube.com/results?search_query={video}'
    webbrowser.open(videos)


@tool
def pesquisar(assunto: str) -> None:
    '''Abre o navegador com os resultados da pesquisa do termo informado.'''
    url = f'https://www.google.com/search?q={assunto}'
    webbrowser.open(url)


@tool
def hora_atual() -> str:
    '''Retorna a hora atual.'''
    return datetime.now().strftime('%H:%M')


@tool
def data_atual() -> str:
    '''Retorna a data atual.'''
    return datetime.now().strftime('%d/%m/%Y')


@tool
def buscar_cotacoes(cotacao: str) -> str:
    '''Retorna a cotação da moeda informada. Porém você deve informar a sigla da moeda, por exemplo: usd, eur, btc, etc.'''     
    url = f'https://economia.awesomeapi.com.br/last/{cotacao}'
    r = requests.get(url)
    
    if r.status_code == 200:
        dados = r.json()
        resultado = dados[cotacao.upper() + 'BRL']['bid']
        resultado = float(resultado)
        return f"R$ {resultado:.2f}"
    else:
        return 'Erro ao buscar cotação.'
    

@tool
def abrir_apps(app: str) -> None:
    '''Abre o aplicativo informado lembrando sempre que estamos no Linux.'''
    os.system(f"{app}")
