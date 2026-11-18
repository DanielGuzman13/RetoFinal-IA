"""Conexión con el servidor MCP de la finca y conversión de sus tools al formato de Ollama."""
import json
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import config

SERVIDOR = config.RAIZ / "mcp_servidor" / "servidor_finca.py"
MAX_CARACTERES_TOOL = 6000  # recorte para no reventar la ventana de contexto


class FincaMCP:
    def __init__(self, sesion: ClientSession, tools):
        self.sesion = sesion
        self.tools = {t.name: t for t in tools}
        self.llamadas = []  # registro de todas las llamadas (para el informe)

    def esquema_ollama(self, nombres=None):
        """Tools en formato de function calling de Ollama, opcionalmente filtradas."""
        salida = []
        for nombre, t in self.tools.items():
            if nombres and nombre not in nombres:
                continue
            salida.append({"type": "function", "function": {
                "name": nombre, "description": t.description or "",
                "parameters": t.inputSchema or {"type": "object", "properties": {}}}})
        return salida

    async def llamar(self, nombre, argumentos, agente=""):
        if isinstance(argumentos, str):
            try:
                argumentos = json.loads(argumentos or "{}")
            except json.JSONDecodeError:
                argumentos = {}
        if nombre not in self.tools:
            texto = json.dumps({"error": f"La herramienta '{nombre}' no existe."}, ensure_ascii=False)
        else:
            try:
                res = await self.sesion.call_tool(nombre, argumentos or {})
                texto = "\n".join(c.text for c in res.content if getattr(c, "text", None))
            except Exception as e:  # el error vuelve al agente para que se corrija
                texto = json.dumps({"error": str(e)}, ensure_ascii=False)
        self.llamadas.append({"agente": agente, "tool": nombre, "argumentos": argumentos,
                              "caracteres_respuesta": len(texto)})
        return texto[:MAX_CARACTERES_TOOL]


@asynccontextmanager
async def conectar():
    params = StdioServerParameters(command=sys.executable, args=[str(SERVIDOR)])
    async with stdio_client(params) as (lectura, escritura):
        async with ClientSession(lectura, escritura) as sesion:
            await sesion.initialize()
            tools = (await sesion.list_tools()).tools
            yield FincaMCP(sesion, tools)
