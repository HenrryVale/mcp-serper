#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Servidor Starlette para MCP-Serper con soporte para Server-Sent Events (SSE).
Este módulo expone las herramientas MCP-Serper a través de una API web.
"""

import os
import json
import uuid
import asyncio
import logging
from typing import Dict, List, Any, Optional, Set, Callable, Awaitable

import uvicorn
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Importar las herramientas MCP-Serper
from mcp_serper import (
    get_docs,
    get_docs_from_domain,
    search_web,
    fetch_url,
    docs_urls
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp-serper-server")

# Permitir nuevas conexiones SSE
allow_new_sse_clients = True

# Clientes SSE activos
sse_clients: Set[str] = set()

# Cola de mensajes para clientes SSE
message_queues: Dict[str, asyncio.Queue] = {}

# Mapa de IDs de cancelación
cancellation_tokens: Dict[str, bool] = {}


async def send_sse_message(client_id: str, data: Any) -> None:
    """
    Envía un mensaje al cliente SSE.
    
    Args:
        client_id: ID del cliente SSE.
        data: Datos a enviar (serán convertidos a JSON).
    """
    if client_id in message_queues:
        message = f"data: {json.dumps(data)}\n\n"
        await message_queues[client_id].put(message)


async def sse_endpoint(request):
    """
    Endpoint para SSE que establece la conexión y transmite eventos al cliente.
    
    Args:
        request: Solicitud HTTP.
        
    Returns:
        Response: Respuesta HTTP con eventos SSE.
    """
    if not allow_new_sse_clients:
        return Response(
            "SSE connections temporarily disabled", 
            status_code=503
        )
    
    client_id = str(uuid.uuid4())
    sse_clients.add(client_id)
    
    # Crear cola de mensajes para este cliente
    queue = asyncio.Queue()
    message_queues[client_id] = queue
    
    # Crear token de cancelación
    cancellation_tokens[client_id] = False
    
    logger.info(f"Nuevo cliente SSE conectado: {client_id}")
    
    async def event_generator():
        try:
            # Mensaje inicial de conexión
            yield f"data: {json.dumps({'type': 'info', 'message': 'Conexión establecida'})}\n\n"
            
            while True:
                if client_id not in sse_clients:
                    break
                
                if cancellation_tokens.get(client_id, False):
                    logger.info(f"Operación cancelada para cliente: {client_id}")
                    yield f"data: {json.dumps({'type': 'info', 'message': 'Operación cancelada'})}\n\n"
                    break
                
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Mantener la conexión con un latido
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
                    continue
        except asyncio.CancelledError:
            logger.info(f"Conexión SSE cancelada para cliente: {client_id}")
        except Exception as e:
            logger.error(f"Error en SSE para cliente {client_id}: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        finally:
            # Limpiar recursos
            if client_id in sse_clients:
                sse_clients.remove(client_id)
            if client_id in message_queues:
                del message_queues[client_id]
            if client_id in cancellation_tokens:
                del cancellation_tokens[client_id]
            logger.info(f"Cliente SSE desconectado: {client_id}")
    
    return Response(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Para Nginx
        },
    )


async def get_docs_stream_endpoint(request):
    """
    Endpoint para obtener documentación de bibliotecas predefinidas con streaming.
    
    Args:
        request: Solicitud HTTP.
        
    Returns:
        JSONResponse: Respuesta JSON con estado de la solicitud.
    """
    try:
        data = await request.json()
        query = data.get("query")
        library = data.get("library")
        
        if not query:
            return JSONResponse({"error": "Se requiere el parámetro 'query'"}, status_code=400)
        if not library:
            return JSONResponse({"error": "Se requiere el parámetro 'library'"}, status_code=400)
        if library not in docs_urls:
            return JSONResponse({"error": f"Biblioteca no soportada: {library}"}, status_code=400)
        
        # Generar ID de cliente para rastrear la solicitud
        client_id = next(iter(request.scope.get("headers", [])), [b"", b""])[1].decode("utf-8")
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Iniciar tarea en segundo plano
        asyncio.create_task(process_docs_request(client_id, query, library))
        
        return JSONResponse({"status": "Procesando", "client_id": client_id})
    
    except Exception as e:
        logger.error(f"Error en get_docs_stream_endpoint: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def get_docs_from_domain_stream_endpoint(request):
    """
    Endpoint para obtener documentación desde un dominio personalizado con streaming.
    
    Args:
        request: Solicitud HTTP.
        
    Returns:
        JSONResponse: Respuesta JSON con estado de la solicitud.
    """
    try:
        data = await request.json()
        query = data.get("query")
        domain = data.get("domain")
        
        if not query:
            return JSONResponse({"error": "Se requiere el parámetro 'query'"}, status_code=400)
        if not domain:
            return JSONResponse({"error": "Se requiere el parámetro 'domain'"}, status_code=400)
        
        # Generar ID de cliente para rastrear la solicitud
        client_id = next(iter(request.scope.get("headers", [])), [b"", b""])[1].decode("utf-8")
        if not client_id:
            client_id = str(uuid.uuid4())
        
        # Iniciar tarea en segundo plano
        asyncio.create_task(process_domain_docs_request(client_id, query, domain))
        
        return JSONResponse({"status": "Procesando", "client_id": client_id})
    
    except Exception as e:
        logger.error(f"Error en get_docs_from_domain_stream_endpoint: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def cancel_operation_endpoint(request):
    """
    Endpoint para cancelar una operación en curso.
    
    Args:
        request: Solicitud HTTP.
        
    Returns:
        JSONResponse: Respuesta JSON con estado de la cancelación.
    """
    try:
        data = await request.json()
        client_id = data.get("client_id")
        
        if not client_id:
            return JSONResponse({"error": "Se requiere el parámetro 'client_id'"}, status_code=400)
        
        if client_id in cancellation_tokens:
            cancellation_tokens[client_id] = True
            return JSONResponse({"status": "Cancelación solicitada"})
        else:
            return JSONResponse({"error": "Cliente no encontrado"}, status_code=404)
    
    except Exception as e:
        logger.error(f"Error en cancel_operation_endpoint: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


async def process_docs_request(client_id: str, query: str, library: str) -> None:
    """
    Procesa una solicitud de documentación y envía resultados a través de SSE.
    
    Args:
        client_id: ID del cliente SSE.
        query: Consulta de búsqueda.
        library: Biblioteca a buscar.
    """
    try:
        await send_sse_message(client_id, {
            "type": "status",
            "message": f"Buscando '{query}' en la documentación de {library}..."
        })
        
        # Inicializar contador de progreso
        current_result = 0
        
        # Función callback para streaming
        async def stream_callback(data, error=False):
            nonlocal current_result
            
            # Verificar cancelación
            if cancellation_tokens.get(client_id, False):
                raise asyncio.CancelledError("Operación cancelada por el usuario")
            
            if error:
                await send_sse_message(client_id, {
                    "type": "error",
                    "message": str(data)
                })
                return
            
            if "progress" in data:
                current_result = data["progress"]["current"]
                total_results = data["progress"]["total"]
                title = data["progress"].get("title", "")
                
                await send_sse_message(client_id, {
                    "type": "progress",
                    "current": current_result,
                    "total": total_results,
                    "title": title
                })
            
            elif "content" in data:
                await send_sse_message(client_id, {
                    "type": "content",
                    "title": data["content"].get("title", "Sin título"),
                    "source": data["content"].get("source", ""),
                    "content": data["content"].get("text", "")
                })
        
        # Llamar a la función MCP con soporte para streaming
        result_data = await get_docs(
            query=query,
            library=library,
            stream_callback=stream_callback,
            with_content=True
        )
        
        # Mensaje de finalización
        await send_sse_message(client_id, {
            "type": "status",
            "message": "Búsqueda completada."
        })
        
    except asyncio.CancelledError:
        logger.info(f"Operación cancelada para cliente: {client_id}")
        await send_sse_message(client_id, {
            "type": "status",
            "message": "Búsqueda cancelada por el usuario."
        })
    except Exception as e:
        logger.error(f"Error en process_docs_request: {str(e)}")
        await send_sse_message(client_id, {
            "type": "error",
            "message": f"Error: {str(e)}"
        })


async def process_domain_docs_request(client_id: str, query: str, domain: str) -> None:
    """
    Procesa una solicitud de documentación desde un dominio personalizado y envía resultados a través de SSE.
    
    Args:
        client_id: ID del cliente SSE.
        query: Consulta de búsqueda.
        domain: Dominio para buscar documentación.
    """
    try:
        await send_sse_message(client_id, {
            "type": "status",
            "message": f"Buscando '{query}' en el dominio: {domain}..."
        })
        
        # Inicializar contador de progreso
        current_result = 0
        
        # Función callback para streaming
        async def stream_callback(data, error=False):
            nonlocal current_result
            
            # Verificar cancelación
            if cancellation_tokens.get(client_id, False):
                raise asyncio.CancelledError("Operación cancelada por el usuario")
            
            if error:
                await send_sse_message(client_id, {
                    "type": "error",
                    "message": str(data)
                })
                return
            
            if "progress" in data:
                current_result = data["progress"]["current"]
                total_results = data["progress"]["total"]
                title = data["progress"].get("title", "")
                
                await send_sse_message(client_id, {
                    "type": "progress",
                    "current": current_result,
                    "total": total_results,
                    "title": title
                })
            
            elif "content" in data:
                await send_sse_message(client_id, {
                    "type": "content",
                    "title": data["content"].get("title", "Sin título"),
                    "source": data["content"].get("source", ""),
                    "content": data["content"].get("text", "")
                })
        
        # Llamar a la función MCP con soporte para streaming
        result_data = await get_docs_from_domain(
            query=query,
            domain=domain,
            stream_callback=stream_callback,
            with_content=True
        )
        
        # Mensaje de finalización
        await send_sse_message(client_id, {
            "type": "status",
            "message": "Búsqueda completada."
        })
        
    except asyncio.CancelledError:
        logger.info(f"Operación cancelada para cliente: {client_id}")
        await send_sse_message(client_id, {
            "type": "status",
            "message": "Búsqueda cancelada por el usuario."
        })
    except Exception as e:
        logger.error(f"Error en process_domain_docs_request: {str(e)}")
        await send_sse_message(client_id, {
            "type": "error",
            "message": f"Error: {str(e)}"
        })


async def health_check(request):
    """
    Endpoint para verificar la salud del servidor.
    
    Args:
        request: Solicitud HTTP.
        
    Returns:
        JSONResponse: Respuesta JSON con estado de salud.
    """
    return JSONResponse({"status": "healthy"})


# Definir rutas
routes = [
    Route("/", endpoint=lambda request: JSONResponse({"message": "API de MCP-Serper"})),
    Route("/health", endpoint=health_check, methods=["GET"]),
    Route("/sse", endpoint=sse_endpoint, methods=["GET"]),
    Route("/messages/get_docs_stream", endpoint=get_docs_stream_endpoint, methods=["POST"]),
    Route("/messages/get_docs_from_domain_stream", endpoint=get_docs_from_domain_stream_endpoint, methods=["POST"]),
    Route("/cancel", endpoint=cancel_operation_endpoint, methods=["POST"]),
    Mount("/demo", StaticFiles(directory="demo"), name="demo"),
]

# Middleware para CORS
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
]

# Crear aplicación Starlette
app = Starlette(
    debug=os.environ.get("DEBUG", "false").lower() == "true",
    routes=routes,
    middleware=middleware,
    on_startup=[],
    on_shutdown=[],
)


def run_server():
    """
    Inicia el servidor Uvicorn.
    """
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    run_server()