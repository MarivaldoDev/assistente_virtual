import json
import os

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

import asyncio

import edge_tts
import pygame
import speech_recognition as sr
from decouple import config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.messages import ToolMessage, HumanMessage

from database import buscas_e_contextos
from utils.functions import *


rec = sr.Recognizer()


class Alexa:
    def __init__(self):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=config("API_KEY"),
            temperature=0.2
        )

        self.tools = [
            temperaturas,
            pesquisar,
            data_atual,
            hora_atual,
            buscar_cotacoes,
            abrir_apps,
            gerar_mensagem_commit
        ]

        self.main()


    def main(self):
        while True:
            print("ouvindo...")
            comando = self.escutar_comando()
            # comando = input(": ")

            if "obrigado" in comando:
                asyncio.run(self.voz_assistente("De nada, estou aqui para ajudar!"))
                break

            resposta = self.assistente(comando)
            asyncio.run(self.voz_assistente(resposta))
            buscas_e_contextos.salvar_memoria(comando, resposta)

    def escapar_chaves(self, texto: str) -> str:
        return texto.replace("{", "{{").replace("}", "}}")



    def assistente(self, comando: str) -> str:
        try:
            contexto = buscas_e_contextos.lembrar_contexto(comando)
        except:
            contexto = None

        prompt = ChatPromptTemplate.from_messages([
            ("system",
            "Você é Alexa, um assistente virtual que responde sempre em português do Brasil.\n"
            "Use ferramentas SOMENTE quando necessário e depois responda ao usuário com um texto natural.\n"
            "Nunca retorne JSON ao usuário."),
            ("system", contexto if contexto else "Sem contexto prévio."),
            MessagesPlaceholder("messages")
        ])

        chain = prompt | self.llm.bind_tools(self.tools)

        primeira_resposta = chain.invoke({
            "messages": [("human", comando)]
        })

        # Caso seja texto direto
        if primeira_resposta.content:
            return primeira_resposta.content

        # Caso seja tool_call
        tool_calls = primeira_resposta.additional_kwargs.get("tool_calls", None)
        if not tool_calls:
            return "Desculpe, não consegui entender sua solicitação."

        tool_call = tool_calls[0]
        tool_id = tool_call["id"]
        tool_name = tool_call["function"]["name"]
        tool_args = tool_call["function"]["arguments"]

        ferramenta = next((t for t in self.tools if t.name == tool_name), None)
        if not ferramenta:
            return f"Erro: ferramenta '{tool_name}' não encontrada."

        try:
            parsed_args = json.loads(tool_args) if isinstance(tool_args, str) else tool_args
        except Exception:
            parsed_args = {}

        resultado = ferramenta.invoke(parsed_args)

        tool_message = ToolMessage(
            content=str(resultado),
            tool_call_id=tool_id,
        )

        segunda_resposta = chain.invoke({
            "messages": [
                HumanMessage(content=comando),
                primeira_resposta,
                tool_message
            ]
        })

        print(segunda_resposta.content)

        return segunda_resposta.content or "Desculpe, não consegui produzir a resposta final."



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
        if not isinstance(texto, str) or texto.strip() == "":
            texto = "Desculpe, ocorreu um erro e não consegui entender a resposta."

        comunicador = edge_tts.Communicate(texto, voice="pt-BR-FranciscaNeural")
        await comunicador.save("voz_ia.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load("voz_ia.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


Alexa()
