"""Servidor MCP de la finca: expone 4 herramientas sobre los datos del laboratorio.

Es la "pequeña parte" de la arquitectura Centinela que se implementa:
los agentes de Red OT y de Dispositivos solo ven la finca a través de estas tools.

Se ejecuta por stdio (lo lanzan los agentes automáticamente):
    python mcp_servidor/servidor_finca.py
"""
import json
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import DATOS  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402

mcp = FastMCP("finca-la-esperanza", log_level="WARNING")

# "Ahora" en el laboratorio = fin de las 24 h simuladas
AHORA = datetime(2026, 11, 18, 6, 0)
# Únicos equipos autorizados para dar órdenes al PLC (política de la finca)
ORIGENES_AUTORIZADOS = {"192.168.10.10"}


def _cargar(nombre):
    with open(DATOS / nombre, encoding="utf-8") as f:
        return json.load(f)


def _hora(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M")


@mcp.tool()
def leer_mqtt(lote: str = "todos", horas: int = 24) -> str:
    """Lee los sensores de humedad del suelo publicados por MQTT.

    Devuelve, por sensor: descripción del dispositivo, estadísticas de las lecturas
    (mínimo, máximo, promedio, desviación) y las primeras/últimas lecturas.
    lote: "todos" o un número de lote del 1 al 5.  horas: ventana hacia atrás (máx. 24).
    """
    desde = AHORA - timedelta(hours=min(max(horas, 1), 24))
    salida = []
    todos = _cargar("mqtt_lecturas.json")
    ultimos_por_tema = {x["tema"]: x["lecturas"][-1]["valor"] for x in todos}
    for s in todos:
        if lote not in ("todos", "", None) and s["tema"] != f"finca/lote{str(lote).strip()}/humedad":
            continue
        lec = [x for x in s["lecturas"] if _hora(x["hora"]) >= desde]
        vals = [x["valor"] for x in lec]
        if not vals:
            continue
        # tramo final sin variación (posible dato congelado o falsificado)
        repetidos = 0
        for v in reversed(vals):
            if v == vals[-1]:
                repetidos += 1
            else:
                break
        salida.append({
            "tema": s["tema"], "dispositivo": s["dispositivo"], "descripcion": s["descripcion"],
            "n_lecturas": len(vals), "min": min(vals), "max": max(vals),
            "promedio": round(statistics.mean(vals), 1),
            "desviacion": round(statistics.pstdev(vals), 2),
            "lecturas_finales_identicas": repetidos,
            "senal_valor_congelado": repetidos >= 12,  # 2 h o más sin ningún cambio
            "promedio_ultimo_valor_otros_lotes": round(statistics.mean(
                v for t, v in ultimos_por_tema.items() if t != s["tema"]), 1),
            "primeras": lec[:3], "ultimas": lec[-3:],
        })
    return json.dumps(salida, ensure_ascii=False)


@mcp.tool()
def leer_modbus_log(horas: int = 24, solo_escrituras: bool = True) -> str:
    """Lee el registro de comandos Modbus enviados al PLC de riego (192.168.10.20).

    Las escrituras (write_coil) abren o cierran válvulas. Devuelve las escrituras completas
    y un resumen de las lecturas por equipo de origen.
    """
    desde = AHORA - timedelta(hours=min(max(horas, 1), 24))
    ev = [e for e in _cargar("modbus_log.json") if _hora(e["hora"]) >= desde]
    escrituras = []
    for e in ev:
        if e["funcion"].startswith("write"):
            hora = _hora(e["hora"]).hour
            escrituras.append({**e, "origen_autorizado": e["origen"] in ORIGENES_AUTORIZADOS,
                               "horario_nocturno": hora >= 22 or hora < 5})
    lecturas = {}
    for e in ev:
        if not e["funcion"].startswith("write"):
            clave = f'{e["equipo_origen"]} ({e["origen"]})'
            lecturas[clave] = lecturas.get(clave, 0) + 1
    res = {"plc": "plc-riego 192.168.10.20",
           "politica": "Solo mini-pc-riego (192.168.10.10) está autorizado para escribir en el PLC",
           "escrituras": escrituras,
           "resumen_lecturas_por_origen": lecturas}
    if not solo_escrituras:
        res["eventos"] = ev
    return json.dumps(res, ensure_ascii=False)


@mcp.tool()
def escanear_dispositivos(red: str = "192.168.10.0/24") -> str:
    """Escanea la red de la finca (simulación de Nmap) y devuelve equipos, puertos,
    producto, versión y notas de las pruebas de configuración."""
    datos = _cargar("dispositivos.json")
    if red.strip() != datos["red"]:
        return json.dumps({"error": f"Red no encontrada. La red de la finca es {datos['red']}"}, ensure_ascii=False)
    return json.dumps(datos, ensure_ascii=False)


@mcp.tool()
def consultar_cve(producto: str, version: str) -> str:
    """Busca vulnerabilidades conocidas (base local simulada) para un producto.
    Devuelve las entradas del producto con su rango de versiones afectadas, para que
    el agente decida si la versión instalada está dentro del rango."""
    p = producto.lower().strip()
    hallados = [c for c in _cargar("cve_db.json") if c["producto"].lower() in p or p in c["producto"].lower()]
    return json.dumps({"producto": producto, "version_instalada": version, "entradas": hallados,
                       "nota": "Compara la versión instalada con versiones_afectadas antes de reportar."},
                      ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()  # transporte stdio
