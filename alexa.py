import speech_recognition as sr
from utiuls.functions import ver_videos, temperaturas, pesquisar, hora_atual, data_atual, buscar_cotacoes, abrir_apps
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from decouple import config
from langchain_groq import ChatGroq
import asyncio
import edge_tts
import pygame
import sqlite3
from difflib import SequenceMatcher


rec = sr.Recognizer()


class Alexa():
    def __init__(self):
        self.main()


    def main(self):
        while True:
            print("ouvindo...")
            #comando = self.escutar_comando()
            comando = input(": ")
            print(comando)

            if "obrigado" in comando:
                asyncio.run(self.voz_assistente("De nada, estou aqui para ajudar!"))
                break

            resposta = self.assistente(comando)
            asyncio.run(self.voz_assistente(resposta))
            self.salvar_memoria(comando, resposta)



    def assistente(self, comando: str) -> str:
        api_key = config("API_KEY")
        llm = ChatGroq(model="llama3-70b-8192", api_key=api_key, temperature=0.2)
        try:
            contexto = self.lembrar_contexto(comando)
        except Exception as e:
            print(f"[Erro ao lembrar contexto]: {e}")
            contexto = None

        mensagens = [
            ("system", "Você é um assistente virtual inteligente que SEMPRE responde em português do Brasil. "
            "Responda de forma clara, tentando ser o mais breve possível, descontraído e NUNCA leia os asteriscos. "
            "Use ferramentas apenas quando for necessário, caso contrário responda com seu próprio conhecimento. "
            "Se houver mensagens anteriores, use-as como referência de contexto."),
        ]

        # Adiciona o contexto como uma 'mensagem do usuário anterior'
        if contexto:
            mensagens.append(("human", contexto))

        # A pergunta atual
        mensagens.append(("human", comando))

        # Placeholder do agente
        mensagens.append(("placeholder", "{agent_scratchpad}"))

        prompt = ChatPromptTemplate.from_messages(mensagens)

        

        tools = [temperaturas, ver_videos, pesquisar, data_atual, hora_atual, buscar_cotacoes, abrir_apps]
        agent = create_tool_calling_agent(
            llm=llm,
            tools=tools,
            prompt=prompt
        )

        agente_executor = AgentExecutor(        
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        try:
            resposta = agente_executor.invoke({
                "input": comando  # Apenas o comando, pois o contexto já está no prompt
            })
            return resposta['output']
        except Exception as e:
            print(f"[Erro no agente]: {e}")
            return llm.invoke(comando)


    def escutar_comando(self) -> str:
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
        

    async def voz_assistente(self, texto: str) -> None:
        comunicador = edge_tts.Communicate(texto, voice="pt-BR-FranciscaNeural")
        await comunicador.save("fala.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load("fala.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


    def salvar_memoria(self, comando: str, resposta: str):
        con = sqlite3.connect('memoria.db')
        cursor = con.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memoria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                comando TEXT NOT NULL,
                resposta TEXT NOT NULL
            )
        ''')

        cursor.execute('INSERT INTO memoria (comando, resposta) VALUES (?, ?)', (comando, resposta))
        con.commit()
        con.close()


    def similaridade(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()


    def lembrar_contexto(self, pergunta_atual: str, limiar: float = 0.6):
        con = sqlite3.connect('memoria.db')
        cursor = con.cursor()
        cursor.execute('SELECT comando, resposta FROM memoria')
        memoria = cursor.fetchall()
        con.close()

        mais_parecido = None
        maior_sim = 0.0

        for comando, resposta in memoria:
            sim = self.similaridade(pergunta_atual, comando)
            if sim > maior_sim and sim >= limiar:
                maior_sim = sim
                mais_parecido = (comando, resposta)

        if mais_parecido:
            comando, resposta = mais_parecido
            return f"Anteriormente, você perguntou: '{comando}' e a resposta foi: '{resposta}'."

        return False


Alexa()
