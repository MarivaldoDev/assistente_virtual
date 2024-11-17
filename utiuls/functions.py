import requests
import webbrowser
import pyttsx3


def temperaturas(cidade: str):
        try:
            api_key = "3d750123dbfeefcba851a398e9d81521"
            site = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&lang=pt_br"

            requisicao = requests.get(site)
            requisicao_dicionario = requisicao.json()
            temperatura = requisicao_dicionario['main']['temp'] - 273.15
        except (requests.ConnectionError, requests.HTTPError):
            return 0
        else:
            return f'{temperatura:.1f}'
        

def ver_videos(video: str):
    videos = f'https://www.youtube.com/results?search_query={video}'
    webbrowser.open(videos)


def pesquisar(assunto: str):
    url = f'https://www.google.com/search?q={assunto}'
    webbrowser.open(url)


def voz(texto: str):
    maquina = pyttsx3.init()
    maquina.say(texto)
    maquina.runAndWait()