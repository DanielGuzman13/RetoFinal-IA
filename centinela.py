"""CENTINELA: ejecuta una revisión de seguridad de la finca y muestra la alerta para el caficultor.

Uso:
    python centinela.py              # modo multiagente (B)
    python centinela.py --modo A     # agente único
    python centinela.py --telegram   # además envía la alerta (requiere TELEGRAM_TOKEN y TELEGRAM_CHAT_ID)
    python centinela.py --peticion "Revisa solo los sensores del lote 3"
"""
import argparse
import json

import config
from agentes import alertas
from agentes.mcp_cliente import conectar
from agentes.modos import PETICION, modo_a, modo_b
from arena import asegurar_datos, ejecutar_seguro


async def revisar(modo, peticion):
    async with conectar() as finca:
        return await (modo_a(finca, peticion) if modo == "A" else modo_b(finca, peticion))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--modo", choices=["A", "B"], default="B")
    p.add_argument("--peticion", default=PETICION)
    p.add_argument("--telegram", action="store_true")
    p.add_argument("--ver-traza", action="store_true", help="muestra qué tools llamó cada agente")
    a = p.parse_args()

    asegurar_datos()
    print(f"Centinela revisando la finca con {config.MODELO} (modo {a.modo})...\n")
    med = ejecutar_seguro(revisar(a.modo, a.peticion))
    if a.ver_traza:
        print("Llamadas a tools MCP:")
        for ll in med["llamadas_tools"]:
            print(f"  [{ll['agente']}] {ll['tool']}({json.dumps(ll['argumentos'], ensure_ascii=False)})")
        print()
    texto = alertas.texto_alerta(med["resultado"])
    print(texto)
    print(f"\n({med['uso']['tokens_totales']} tokens, {med['segundos_totales']} s)")
    if a.telegram:
        print("Telegram:", "enviado" if alertas.enviar_telegram(texto) else "no configurado o falló")


if __name__ == "__main__":
    main()
