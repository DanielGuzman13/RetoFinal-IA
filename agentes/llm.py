"""Cliente mínimo de Ollama (API /api/chat) con soporte de tools y medición de uso."""
from __future__ import annotations
import time
from dataclasses import dataclass, field

import requests

import config


@dataclass
class Uso:
    """Acumula tokens y tiempo de todas las llamadas al modelo."""
    tokens_entrada: int = 0
    tokens_salida: int = 0
    segundos: float = 0.0
    llamadas: int = 0
    detalle: list = field(default_factory=list)

    def sumar(self, otro: "Uso"):
        self.tokens_entrada += otro.tokens_entrada
        self.tokens_salida += otro.tokens_salida
        self.segundos += otro.segundos
        self.llamadas += otro.llamadas
        self.detalle.extend(otro.detalle)

    @property
    def tokens_totales(self):
        return self.tokens_entrada + self.tokens_salida


def chat(mensajes, tools=None, modelo=None, uso: Uso | None = None, etiqueta="", formato_json=False):
    """Llama a Ollama. Devuelve el mensaje del asistente (dict con content y tool_calls)."""
    cuerpo = {
        "model": modelo or config.MODELO,
        "messages": mensajes,
        "stream": False,
        "options": {"temperature": config.TEMPERATURA, "num_ctx": config.NUM_CTX},
    }
    if tools:
        cuerpo["tools"] = tools
    if formato_json:
        cuerpo["format"] = "json"
    t0 = time.perf_counter()
    try:
        r = requests.post(f"{config.OLLAMA_URL}/api/chat", json=cuerpo, timeout=config.TIMEOUT_LLM_S)
    except requests.ConnectionError as e:
        raise RuntimeError(
            f"No pude conectar con Ollama en {config.OLLAMA_URL}. ¿Está abierto Ollama?"
        ) from e
    if r.status_code == 404:
        raise RuntimeError(f"Ollama no tiene el modelo '{cuerpo['model']}'. Ejecuta: ollama pull {cuerpo['model']}")
    r.raise_for_status()
    datos = r.json()
    seg = time.perf_counter() - t0
    if uso is not None:
        te, ts = datos.get("prompt_eval_count", 0) or 0, datos.get("eval_count", 0) or 0
        uso.tokens_entrada += te
        uso.tokens_salida += ts
        uso.segundos += seg
        uso.llamadas += 1
        uso.detalle.append({"etiqueta": etiqueta, "tokens_entrada": te, "tokens_salida": ts,
                            "segundos": round(seg, 2)})
    return datos.get("message", {})
