# Centinela — Finca La Esperanza

Sistema agéntico de ciberseguridad para una finca cafetera con IoT (caso ficticio), con:

- un **servidor MCP** que expone la finca a los agentes (4 tools),
- un **agente único** (modo A) y un **equipo multiagente** (modo B),
- un **agente juez** que mide calidad y costo,
- todo con **modelos locales** en Ollama. Ningún dato sale del computador.

Los datos de la finca (24 h de sensores, comandos al riego, escaneo de red) son **simulados** y traen 5 fallas plantadas a propósito, que sirven de verdad base para medir la calidad.

## 1. Instalación (Windows, una sola vez)

1. **Ollama:** descárgalo de https://ollama.com/download e instálalo. Luego, en PowerShell:
   ```powershell
   ollama pull qwen2.5:7b
   ```
   El modelo pesa unos 4,7 GB. Si tu equipo tiene poca RAM o no tiene GPU, usa `qwen2.5:3b` (ver la sección 4).

2. **Python 3.10 o superior** (sirve el de Anaconda). En PowerShell:
   ```powershell
   cd $HOME\Documents\reto-centinela-finca
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Si PowerShell bloquea `activate`, ejecuta una vez: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 2. Uso

Con Ollama abierto y el entorno activado (`.venv\Scripts\activate`):

```powershell
# 1. Generar los datos simulados de la finca (se hace solo si no existen)
python laboratorio\simulador.py

# 2. Una revisión de seguridad completa (multiagente) y la alerta para el caficultor
python centinela.py --ver-traza

#    La misma revisión con un solo agente
python centinela.py --modo A --ver-traza

# 3. El experimento: compara A vs B, 3 repeticiones cada uno
python arena.py
python arena.py --repeticiones 1 --sin-juez-llm   # versión rápida
```

`arena.py` deja en `resultados\<fecha>\`:
- `informe.md`: tabla comparativa, hallazgos de cada modo y cómo se midió (lista para la entrega),
- `resultados.json`: todos los datos crudos (tokens por llamada, tools llamadas, trazas),
- `alerta_modo_A.txt` y `alerta_modo_B.txt`: el mensaje que recibiría el administrador.

## 3. Cómo se relaciona con el diagrama

| Diagrama | Archivo |
|---|---|
| Datos de la finca (sensores, PLC, cámaras) | `laboratorio/simulador.py` → `datos/` |
| Prototipo MCP (servidor con 4 tools) | `mcp_servidor/servidor_finca.py` |
| Agentes Red OT y Dispositivos, orquestador | `agentes/modos.py` (modo B) y `agentes/agente.py` |
| Modo A: agente único | `agentes/modos.py` (`modo_a`) |
| Agente juez (evaluador) | `agentes/juez.py` |
| Alertas al caficultor | `agentes/alertas.py` |
| Arena | `arena.py` |

Las tools MCP son:

| Tool | Qué devuelve |
|---|---|
| `leer_mqtt(lote, horas)` | Estadísticas de los sensores de humedad y la descripción de cada dispositivo |
| `leer_modbus_log(horas)` | Comandos de escritura enviados al PLC de riego y quién los envió |
| `escanear_dispositivos(red)` | Equipos, puertos, versiones y pruebas de configuración (simula Nmap) |
| `consultar_cve(producto, version)` | Vulnerabilidades conocidas (base local simulada, ids `CVE-SIM-*`) |

Las 5 fallas plantadas (verdad base, en `datos/verdad_base.json`):

| Id | Falla | Tema del reto |
|---|---|---|
| F1 | Cámara de la bodega con clave de fábrica admin/admin | Ciberseguridad clásica |
| F2 | Comando Modbus que abre la válvula del lote 3 a las 02:14 desde el PC de oficina | Seguridad OT |
| F3 | Broker MQTT que acepta conexiones anónimas | Seguridad IoT |
| F4 | Sensor del lote 3 falsificado (5 % fijo) que engaña a la IA de riego | Uso de la IA |
| F5 | Instrucción oculta en la descripción del sensor del lote 5 | Ataques a agentes |

## 4. Configuración

Todo se cambia con variables de entorno (ver `config.py`). En PowerShell:

```powershell
$env:MODELO = "qwen2.5:3b"        # modelo de los agentes
$env:MODELO_JUEZ = "qwen2.5:7b"   # modelo del juez (puede ser otro)
$env:POTENCIA_W = "45"            # consumo de tu equipo mientras corre el modelo
$env:TARIFA_KWH_COP = "950"       # tarifa de tu factura de energía
```

Comparar modelos además de modos es tan simple como correr `arena.py` con distintos `MODELO`.

**Costo.** Con modelos locales no se paga por token. El costo se estima como potencia × tiempo × tarifa del kWh. Como referencia, el informe muestra cuánto costarían los mismos tokens en una API de nube, con precios de ejemplo que puedes ajustar en `config.py`.

**Telegram (opcional).** Crea un bot con @BotFather, define `$env:TELEGRAM_TOKEN` y `$env:TELEGRAM_CHAT_ID`, y ejecuta `python centinela.py --telegram`.
