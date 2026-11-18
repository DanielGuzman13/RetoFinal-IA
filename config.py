"""Configuración central del proyecto Centinela - Finca La Esperanza.

Todos los valores se pueden cambiar con variables de entorno sin tocar el código.
"""
import os
import sys
from pathlib import Path

# Consola de Windows: forzar UTF-8 para tildes y emojis
for _flujo in (sys.stdout, sys.stderr):
    try:
        _flujo.reconfigure(encoding="utf-8")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos"
RESULTADOS = RAIZ / "resultados"

# --- Modelo local (Ollama) ---
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODELO = os.getenv("MODELO", "qwen2.5:7b")            # agentes
MODELO_JUEZ = os.getenv("MODELO_JUEZ", MODELO)         # agente juez
NUM_CTX = int(os.getenv("NUM_CTX", "8192"))            # ventana de contexto
TEMPERATURA = float(os.getenv("TEMPERATURA", "0.2"))
MAX_PASOS = int(os.getenv("MAX_PASOS", "8"))           # llamadas a tools por agente
TIMEOUT_LLM_S = int(os.getenv("TIMEOUT_LLM_S", "600"))
# Obliga a cada agente a usar todas sus tools antes de concluir (0 para desactivar)
COBERTURA_MINIMA = os.getenv("COBERTURA_MINIMA", "1") == "1"

# --- Costo (modelos locales: se paga energía, no tokens) ---
# Potencia promedio del equipo mientras el modelo trabaja (W). Un portátil con GPU
# suele estar entre 40 y 120 W; un mini PC o Jetson entre 15 y 60 W. Ajústalo.
POTENCIA_W = float(os.getenv("POTENCIA_W", "60"))
# Tarifa del kWh en COP. Valor de ejemplo: cámbialo por el de tu factura.
TARIFA_KWH_COP = float(os.getenv("TARIFA_KWH_COP", "900"))

# Referencia: cuánto costarían los mismos tokens en una API de nube.
# Valores de ejemplo, configurables; no corresponden a un proveedor específico.
PRECIO_API_USD_1M_ENTRADA = float(os.getenv("PRECIO_API_USD_1M_ENTRADA", "0.50"))
PRECIO_API_USD_1M_SALIDA = float(os.getenv("PRECIO_API_USD_1M_SALIDA", "1.50"))
TRM_COP_USD = float(os.getenv("TRM_COP_USD", "4000"))

# --- Alertas (opcional) ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
