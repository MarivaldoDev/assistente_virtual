from utiuls.functions import temperaturas, ver_videos, pesquisar, voz
import speech_recognition as sr
import datetime
import pywhatkit
import pyautogui as pa
import os


rec = sr.Recognizer()


class Alexa():
    def __init__(self):
        self.main()
        self.executar()
 

    def executar(self):
        while True:
            try:
                with sr.Microphone() as mic:
                    rec.adjust_for_ambient_noise(mic)
                    audio = rec.listen(mic)
                    texto = rec.recognize_google(audio, language="pt-BR")
            except sr.UnknownValueError:
                print("Não foi possível entender o áudio.")
                continue
            except sr.RequestError:
                print("Erro ao acessar o serviço de reconhecimento de fala.")
                continue
            else:
                if "Alexa" in texto:
                    texto = texto.replace('Alexa', '')

            return texto.lower()



    def main(self):
        voz("olá! como posso ajudar?")
        
        while True:
            print("ouvindo...")
            comando = self.executar()

            if "obrigado" in comando or "obrigado alexa" in comando:
                voz("estou sempre a disposição")
                break

            elif "seu nome" in comando:
                voz("sou a assistente virtual do senhor pedro")

            elif "horas" in comando:
                hora = datetime.datetime.now().strftime('%H:%M')
                voz(f"São {hora}")

            elif "dia" in comando:
                dia = datetime.datetime.now().day
                mes = datetime.datetime.now().month
                
                voz(f"Hoje é dia {dia} do mês {mes}")

            elif "procure por" in comando or "pesquise por" in comando:
                pesquisa = comando.replace("procure por", "")
                pesquisar(pesquisa)
                voz(f"resultado sobre {pesquisa}")

            elif "temperatura" in comando:
                with sr.Microphone() as mic:
                    rec.adjust_for_ambient_noise(mic)
                    voz("qual sua cidade?")
                    
                    audio = rec.listen(mic)
                    texto = rec.recognize_google(audio, language="pt-BR")
                
                if temperaturas(texto) == 0:
                    voz("desculpe! não é possível ter a informação sem internet.")
                else:
                    voz(f"A temperatura em {texto} nesse momento é de {temperaturas(texto)}°")

            elif "toque" in comando:
                musica = comando.replace("toque", "")
                pywhatkit.playonyt(musica)
                
                voz(f"tocando {musica}")

            elif "me mostre" in comando:
                comando = comando.replace("me mostre", "")
                ver_videos(comando)
                voz(f"resultado sobre {comando}")

            elif "abrir" in comando:
                app = comando.replace("abrir", "")
                voz(f"abrindo {app}")
                os.system(f'start {app}')

            elif "desligar computador" in comando:
                voz("Desligando...")
                pa.PAUSE = 0.5
                pa.hotkey('alt', 'f4')
                pa.press('enter')
            else:
                voz("não entendi o comando! repita por favor.")


Alexa()
