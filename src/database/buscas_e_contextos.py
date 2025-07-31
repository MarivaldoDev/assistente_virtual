import sqlite3
from difflib import SequenceMatcher


def salvar_memoria(comando: str, resposta: str):
    con = sqlite3.connect("memoria.db")
    cursor = con.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS memoria (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            comando TEXT NOT NULL,
            resposta TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        "INSERT INTO memoria (comando, resposta) VALUES (?, ?)", (comando, resposta)
    )
    con.commit()

    con.close()


def similaridade(a: str, b: str) -> float:

    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def lembrar_contexto(pergunta_atual: str, limiar: float = 0.6):
    con = sqlite3.connect("memoria.db")
    cursor = con.cursor()
    cursor.execute("SELECT comando, resposta FROM memoria")
    memoria = cursor.fetchall()
    con.close()

    mais_parecido = None
    maior_sim = 0.0

    for comando, resposta in memoria:
        sim = similaridade(pergunta_atual, comando)
        if sim > maior_sim and sim >= limiar:
            maior_sim = sim
            mais_parecido = (comando, resposta)

    if mais_parecido:
        comando, resposta = mais_parecido
        return f"Anteriormente, você perguntou: '{comando}' e a resposta foi: '{resposta}'."

    return False
