"""Convierte el resultado en la alerta corta para el caficultor y, si se configura, la envía por Telegram."""
import requests

import config

ORDEN = {"CRITICO": 0, "CRÍTICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}
ICONO = {0: "🔴", 1: "🟠", 2: "🟡", 3: "⚪"}


def ordenar(hallazgos):
    return sorted([h for h in hallazgos if isinstance(h, dict)],
                  key=lambda h: ORDEN.get(str(h.get("severidad", "")).upper(), 4))


def texto_alerta(resultado, fecha="18 nov 2026, 6:02 a. m."):
    lineas = [f"🚨 Centinela — Finca La Esperanza — {fecha}", ""]
    if resultado.get("resumen"):
        lineas += [resultado["resumen"].strip(), ""]
    for h in ordenar(resultado.get("hallazgos", []))[:6]:
        n = ORDEN.get(str(h.get("severidad", "")).upper(), 3)
        lineas.append(f"{ICONO.get(n, '⚪')} {h.get('titulo', 'Hallazgo')}")
        if h.get("accion"):
            lineas.append(f"   → {h['accion']}")
    if not resultado.get("hallazgos"):
        lineas.append("Sin hallazgos en esta revisión.")
    return "\n".join(lineas)


def enviar_telegram(texto):
    if not (config.TELEGRAM_TOKEN and config.TELEGRAM_CHAT_ID):
        return False
    r = requests.post(f"https://api.telegram.org/bot{config.TELEGRAM_TOKEN}/sendMessage",
                      json={"chat_id": config.TELEGRAM_CHAT_ID, "text": texto}, timeout=20)
    return r.ok
