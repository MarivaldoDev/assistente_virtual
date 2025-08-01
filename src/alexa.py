import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import asyncio

import edge_tts
import pygame
import speech_recognition as sr
from decouple import config
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq

from database import buscas_e_contextos
from utils.functions import *


rec = sr.Recognizer()


class Alexa:
    def __init__(self):
        self.main()

    def main(self):
        while True:
            print("ouvindo...")
            # comando = self.escutar_comando()
            comando = input(": ")

            if "obrigado" in comando:
                asyncio.run(self.voz_assistente("De nada, estou aqui para ajudar!"))
                break

            resposta = self.assistente(comando)
            asyncio.run(self.voz_assistente(resposta))
            buscas_e_contextos.salvar_memoria(comando, resposta)

    def escapar_chaves(self, texto: str) -> str:
        return texto.replace("{", "{{").replace("}", "}}")

    def assistente(self, comando: str) -> str:
        api_key = config("API_KEY")
        self.llm = ChatGroq(model="llama3-70b-8192", api_key=api_key, temperature=0.2)
        try:
            contexto = buscas_e_contextos.lembrar_contexto(comando)
        except Exception as e:
            print(f"[Erro ao lembrar contexto]: {e}")
            contexto = None

        mensagens = [
            (
                "system",
                (
                    "Você é Alexa, um assistente virtual inteligente que SEMPRE responde em português do Brasil. "
                    "Seja claro, breve, amigável e NUNCA leia ou mencione asteriscos. "
                    "Use ferramentas apenas quando necessário e explique de forma simples quando usar uma ferramenta. "
                    "Seja descontraído, mas profissional. "
                    "Se houver mensagens anteriores, utilize-as como contexto para melhorar sua resposta. "
                    "Nunca invente informações e, se não souber, diga que não sabe. "
                    "Se o usuário pedir para executar uma ação (como abrir apps, buscar vídeos, consultar temperatura, etc), utilize as ferramentas disponíveis. "
                    "Caso a resposta seja apenas informativa, responda com seu próprio conhecimento."
                ),
            ),
        ]

        if contexto:
            mensagens.append(("human", self.escapar_chaves(contexto)))

        mensagens.append(("human", self.escapar_chaves(comando)))

        mensagens.append(MessagesPlaceholder(variable_name="agent_scratchpad"))

        prompt = ChatPromptTemplate.from_messages(mensagens)

        tools = [
            temperaturas,
            ver_videos,
            pesquisar,
            data_atual,
            hora_atual,
            buscar_cotacoes,
            abrir_apps,
            gerar_mensagem_commit,
        ]
        agent = create_tool_calling_agent(llm=self.llm, tools=tools, prompt=prompt)

        agente_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
        )

        try:
            resposta = agente_executor.invoke(
                {
                    "input": comando  # Apenas o comando, pois o contexto já está no prompt
                }
            )
            return resposta["output"]
        except Exception as e:
            print(f"[Erro ao executar agente]: {e}")

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
                    texto = texto.replace("Alexa", "")

            return texto.lower()

    async def voz_assistente(self, texto: str) -> None:
        comunicador = edge_tts.Communicate(texto, voice="pt-BR-FranciscaNeural")
        await comunicador.save(r"voz_ia.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load(r"voz_ia.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


Alexa()
