import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"

import speech_recognition as sr
from utiuls.functions import *
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from decouple import config
from langchain_groq import ChatGroq
import asyncio
import edge_tts
import pygame
from database import buscas_e_contextos
from langchain_core.prompts import MessagesPlaceholder



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
            ("system", (
                "Você é Alexa, um assistente virtual inteligente que SEMPRE responde em português do Brasil. "
                "Seja claro, breve, amigável e NUNCA leia ou mencione asteriscos. "
                "Use ferramentas apenas quando necessário e explique de forma simples quando usar uma ferramenta. "
                "Seja descontraído, mas profissional. "
                "Se houver mensagens anteriores, utilize-as como contexto para melhorar sua resposta. "
                "Nunca invente informações e, se não souber, diga que não sabe. "
                "Se o usuário pedir para executar uma ação (como abrir apps, buscar vídeos, consultar temperatura, etc), utilize as ferramentas disponíveis. "
                "Caso a resposta seja apenas informativa, responda com seu próprio conhecimento."
            )),
        ]

        if contexto:
            mensagens.append(("human", self.escapar_chaves(contexto)))

        mensagens.append(("human", self.escapar_chaves(comando)))

        mensagens.append(MessagesPlaceholder(variable_name="agent_scratchpad"))

        prompt = ChatPromptTemplate.from_messages(mensagens)

        

        tools = [temperaturas, ver_videos, pesquisar, data_atual, hora_atual, buscar_cotacoes, abrir_apps, gerar_mensagem_commit]
        agent = create_tool_calling_agent(
            llm=self.llm,
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
            return self.llm.invoke(comando)


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
        await comunicador.save(r"audio/fala.mp3")

        pygame.mixer.init()
        pygame.mixer.music.load(r"audio/fala.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)


   


Alexa()
