#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MCP-Serper: Herramienta para buscar documentación técnica usando Google Serper API.

Este módulo proporciona herramientas para buscar documentación técnica usando Google Serper API
a través del protocolo MCP (Model Control Protocol).
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Awaitable
from urllib.parse import urlparse, quote_plus

import httpx
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp-serper")

# APIs y Claves
SERPER_API_KEY = os.environ.get("SERPER_API_KEY")
SERPER_API_URL = "https://google.serper.dev/search"

# Biblioteca de URLs de documentación
docs_urls = {
    "python": "docs.python.org",
    "javascript": "developer.mozilla.org",
    "typescript": "www.typescriptlang.org",
    "react": "reactjs.org",
    "vue": "vuejs.org",
    "angular": "angular.io",
    "django": "docs.djangoproject.com",
    "flask": "flask.palletsprojects.com",
    "fastapi": "fastapi.tiangolo.com",
    "nodejs": "nodejs.org",
    "go": "golang.org",
    "rust": "doc.rust-lang.org",
    "swift": "developer.apple.com",
    "kotlin": "kotlinlang.org",
    "pandas": "pandas.pydata.org",
    "numpy": "numpy.org",
    "matplotlib": "matplotlib.org",
    "tensorflow": "www.tensorflow.org",
    "pytorch": "pytorch.org",
    "scikit-learn": "scikit-learn.org",
    "spring": "spring.io",
    "laravel": "laravel.com",
    "dotnet": "docs.microsoft.com/dotnet",
    "csharp": "docs.microsoft.com/csharp",
    "java": "docs.oracle.com/javase",
    "cpp": "en.cppreference.com",
    "c": "en.cppreference.com",
    "sql": "www.w3schools.com/sql",
    "mysql": "dev.mysql.com",
    "postgresql": "www.postgresql.org",
    "mongodb": "docs.mongodb.com",
    "redis": "redis.io",
    "docker": "docs.docker.com",
    "kubernetes": "kubernetes.io",
    "aws": "docs.aws.amazon.com",
    "azure": "docs.microsoft.com/azure",
    "gcp": "cloud.google.com",
    "linux": "man7.org",
    "git": "git-scm.com",
    "html": "developer.mozilla.org/html",
    "css": "developer.mozilla.org/css",
    "bootstrap": "getbootstrap.com",
    "tailwind": "tailwindcss.com",
    "sass": "sass-lang.com",
    "jquery": "api.jquery.com",
    "webpack": "webpack.js.org",
    "vite": "vitejs.dev",
    "npm": "docs.npmjs.com",
    "yarn": "yarnpkg.com",
    "pip": "pip.pypa.io",
    "conda": "docs.conda.io",
    "virtualenv": "virtualenv.pypa.io",
    "venv": "docs.python.org/3/library/venv.html",
    "ruby": "ruby-doc.org",
    "rails": "guides.rubyonrails.org",
    "php": "www.php.net",
    "symfony": "symfony.com",
    "wordpress": "wordpress.org",
    "drupal": "www.drupal.org",
    "jupyter": "jupyter.org",
    "anaconda": "docs.anaconda.com",
    "hadoop": "hadoop.apache.org",
    "spark": "spark.apache.org",
    "powerbi": "docs.microsoft.com/power-bi",
    "tableau": "help.tableau.com",
    "excel": "support.microsoft.com/excel",
    "unity": "docs.unity3d.com",
    "godot": "docs.godotengine.org",
    "vulkan": "www.khronos.org/vulkan",
    "opengl": "www.khronos.org/opengl",
    "directx": "docs.microsoft.com/directx",
    "postgresql": "www.postgresql.org/docs",
    "mysql": "dev.mysql.com/doc",
    "sqlite": "www.sqlite.org/docs.html",
    "oracle": "docs.oracle.com/database",
    "graphql": "graphql.org",
    "apollo": "www.apollographql.com/docs",
    "relay": "relay.dev/docs",
    "nextjs": "nextjs.org/docs",
    "gatsbyjs": "www.gatsbyjs.com/docs",
    "svelte": "svelte.dev/docs",
    "nuxtjs": "nuxtjs.org/docs",
    "remix": "remix.run/docs",
    "vuepress": "vuepress.vuejs.org",
    "numpy": "numpy.org/doc",
    "pandas": "pandas.pydata.org/docs",
    "scipy": "docs.scipy.org/doc",
    "matplotlib": "matplotlib.org/stable/contents.html",
    "seaborn": "seaborn.pydata.org",
    "plotly": "plotly.com/python",
    "dash": "dash.plotly.com",
    "streamlit": "docs.streamlit.io",
    "gradio": "gradio.app/docs",
    "selenium": "www.selenium.dev/documentation",
    "puppeteer": "pptr.dev",
    "cypress": "docs.cypress.io",
    "jest": "jestjs.io/docs",
    "mocha": "mochajs.org",
    "pytest": "docs.pytest.org",
    "jasmine": "jasmine.github.io",
}

# Caché en memoria para respuestas
results_cache = {}


async def search_web(
    query: str,
    site: Optional[str] = None,
    num_results: int = 10,
    timeout: int = 30,
) -> Dict[str, Any]:
    """
    Realiza una búsqueda en la web usando Google Serper API.
    
    Args:
        query: Consulta de búsqueda.
        site: Dominio específico para buscar.
        num_results: Número de resultados a devolver.
        timeout: Tiempo máximo de espera en segundos.
        
    Returns:
        Dict: Resultados de la búsqueda.
        
    Raises:
        Exception: Si ocurre un error durante la búsqueda.
    """
    if not SERPER_API_KEY:
        raise Exception("SERPER_API_KEY no está configurado. Defina esta variable de entorno.")
    
    # Construir la consulta con el sitio específico
    search_query = query
    if site:
        search_query = f"site:{site} {query}"
    
    # Preparar la solicitud
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "q": search_query,
        "num": num_results,
    }
    
    cache_key = f"{search_query}_{num_results}"
    
    # Verificar caché
    if cache_key in results_cache:
        logger.info(f"Recuperando resultados de caché para: {search_query}")
        return results_cache[cache_key]
    
    # Realizar la solicitud
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                SERPER_API_URL,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Almacenar en caché
                results_cache[cache_key] = result
                
                return result
            else:
                error_msg = f"Error en Serper API: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
    
    except httpx.TimeoutException:
        raise Exception(f"Tiempo de espera agotado al consultar la API. Timeout: {timeout}s")
    
    except Exception as e:
        logger.error(f"Error inesperado al buscar en la web: {str(e)}")
        raise Exception(f"Error al buscar en la web: {str(e)}")


async def fetch_url(
    url: str,
    timeout: int = 30,
    max_content_length: int = 500000  # ~500KB
) -> Dict[str, str]:
    """
    Recupera el contenido de una URL.
    
    Args:
        url: URL a recuperar.
        timeout: Tiempo máximo de espera en segundos.
        max_content_length: Tamaño máximo de contenido a recuperar en bytes.
        
    Returns:
        Dict: Título y contenido de la página.
        
    Raises:
        Exception: Si ocurre un error durante la recuperación.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=headers,
                timeout=timeout,
                follow_redirects=True
            )
            
            if response.status_code != 200:
                return {
                    "title": f"Error {response.status_code}",
                    "content": f"No se pudo obtener el contenido: {response.status_code} - {response.reason_phrase}"
                }
            
            if int(response.headers.get("content-length", 0)) > max_content_length:
                return {
                    "title": "Contenido demasiado grande",
                    "content": f"El contenido de la página excede el tamaño máximo permitido de {max_content_length // 1024}KB."
                }
            
            # Procesar el contenido HTML
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Extraer título
            title = soup.title.string if soup.title else "Sin título"
            
            # Extraer contenido principal
            # Intentar encontrar el contenido principal
            main_content = soup.find("main") or soup.find("article") or soup.find("div", class_=["content", "main", "article"])
            
            if not main_content:
                main_content = soup.body
            
            # Eliminar scripts, estilos y comentarios
            for element in main_content(["script", "style", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Extraer texto
            content = main_content.get_text(separator=" ", strip=True)
            
            # Limpiar espacios excesivos y saltos de línea
            import re
            content = re.sub(r'\s+', ' ', content).strip()
            
            return {
                "title": title,
                "content": content,
                "url": str(response.url)
            }
    
    except httpx.TimeoutException:
        return {
            "title": "Tiempo de espera agotado",
            "content": f"No se pudo obtener el contenido dentro del tiempo límite de {timeout} segundos."
        }
    
    except Exception as e:
        logger.error(f"Error al recuperar URL {url}: {str(e)}")
        return {
            "title": "Error al recuperar contenido",
            "content": f"Ocurrió un error: {str(e)}"
        }


async def get_docs(
    query: str,
    library: str,
    num_results: int = 5,
    with_content: bool = False,
    stream_callback: Optional[Callable[[Dict[str, Any], bool], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Busca documentación para una consulta específica en una biblioteca.
    
    Args:
        query: Consulta de búsqueda.
        library: Biblioteca para buscar (debe estar en docs_urls).
        num_results: Número de resultados a devolver.
        with_content: Si es True, incluye el contenido de cada resultado.
        stream_callback: Función de callback para streaming de resultados.
        
    Returns:
        Dict: Resultados de la búsqueda.
        
    Raises:
        Exception: Si la biblioteca no está soportada o si ocurre un error durante la búsqueda.
    """
    if library not in docs_urls:
        error_msg = f"Biblioteca no soportada: {library}. Las bibliotecas soportadas son: {', '.join(docs_urls.keys())}"
        if stream_callback:
            await stream_callback(error_msg, error=True)
        raise Exception(error_msg)
    
    site = docs_urls[library]
    
    try:
        # Buscar resultados
        search_results = await search_web(query, site, num_results)
        
        # Extraer enlaces orgánicos
        organic_results = search_results.get("organic", [])
        
        results = []
        
        # Informar del total de resultados
        total_results = min(len(organic_results), num_results)
        if stream_callback:
            await stream_callback({
                "progress": {
                    "current": 0,
                    "total": total_results,
                    "title": f"Encontrados {total_results} resultados para '{query}' en {library}"
                }
            })
        
        # Procesar cada resultado
        for i, result in enumerate(organic_results[:num_results]):
            title = result.get("title", "Sin título")
            link = result.get("link", "")
            snippet = result.get("snippet", "Sin descripción")
            
            # Informar del progreso
            if stream_callback:
                await stream_callback({
                    "progress": {
                        "current": i + 1,
                        "total": total_results,
                        "title": title
                    }
                })
            
            result_item = {
                "title": title,
                "url": link,
                "snippet": snippet
            }
            
            # Opcionalmente recuperar el contenido completo
            if with_content and link:
                content_data = await fetch_url(link)
                result_item["content"] = content_data.get("content", "")
                
                # Enviar contenido al callback si existe
                if stream_callback:
                    await stream_callback({
                        "content": {
                            "title": title,
                            "source": link,
                            "text": content_data.get("content", "")
                        }
                    })
            
            results.append(result_item)
        
        return {
            "results": results,
            "total": len(results),
            "library": library,
            "query": query
        }
    
    except Exception as e:
        error_msg = f"Error al buscar documentación: {str(e)}"
        logger.error(error_msg)
        if stream_callback:
            await stream_callback(error_msg, error=True)
        raise Exception(error_msg)


async def get_docs_from_domain(
    query: str,
    domain: str,
    num_results: int = 5,
    with_content: bool = False,
    stream_callback: Optional[Callable[[Dict[str, Any], bool], Awaitable[None]]] = None
) -> Dict[str, Any]:
    """
    Busca documentación para una consulta específica en un dominio personalizado.
    
    Args:
        query: Consulta de búsqueda.
        domain: Dominio específico para buscar.
        num_results: Número de resultados a devolver.
        with_content: Si es True, incluye el contenido de cada resultado.
        stream_callback: Función de callback para streaming de resultados.
        
    Returns:
        Dict: Resultados de la búsqueda.
        
    Raises:
        Exception: Si ocurre un error durante la búsqueda.
    """
    # Validar dominio
    if not domain or "." not in domain:
        error_msg = f"Dominio no válido: {domain}. Debe ser un dominio válido como 'example.com'."
        if stream_callback:
            await stream_callback(error_msg, error=True)
        raise Exception(error_msg)
    
    # Extraer el dominio base
    parsed_domain = urlparse(domain)
    base_domain = parsed_domain.netloc or parsed_domain.path
    
    try:
        # Buscar resultados
        search_results = await search_web(query, base_domain, num_results)
        
        # Extraer enlaces orgánicos
        organic_results = search_results.get("organic", [])
        
        results = []
        
        # Informar del total de resultados
        total_results = min(len(organic_results), num_results)
        if stream_callback:
            await stream_callback({
                "progress": {
                    "current": 0,
                    "total": total_results,
                    "title": f"Encontrados {total_results} resultados para '{query}' en {base_domain}"
                }
            })
        
        # Procesar cada resultado
        for i, result in enumerate(organic_results[:num_results]):
            title = result.get("title", "Sin título")
            link = result.get("link", "")
            snippet = result.get("snippet", "Sin descripción")
            
            # Informar del progreso
            if stream_callback:
                await stream_callback({
                    "progress": {
                        "current": i + 1,
                        "total": total_results,
                        "title": title
                    }
                })
            
            result_item = {
                "title": title,
                "url": link,
                "snippet": snippet
            }
            
            # Opcionalmente recuperar el contenido completo
            if with_content and link:
                content_data = await fetch_url(link)
                result_item["content"] = content_data.get("content", "")
                
                # Enviar contenido al callback si existe
                if stream_callback:
                    await stream_callback({
                        "content": {
                            "title": title,
                            "source": link,
                            "text": content_data.get("content", "")
                        }
                    })
            
            results.append(result_item)
        
        return {
            "results": results,
            "total": len(results),
            "domain": base_domain,
            "query": query
        }
    
    except Exception as e:
        error_msg = f"Error al buscar documentación: {str(e)}"
        logger.error(error_msg)
        if stream_callback:
            await stream_callback(error_msg, error=True)
        raise Exception(error_msg)


# Exposición de herramientas para MCP
async def mcp__get_docs(
    query: str,
    library: str,
    num_results: int = 5,
    with_content: bool = False
) -> Dict[str, Any]:
    """
    Herramienta MCP para buscar documentación para una consulta específica en una biblioteca.
    
    Args:
        query: Consulta de búsqueda.
        library: Biblioteca para buscar (debe estar en docs_urls).
        num_results: Número de resultados a devolver.
        with_content: Si es True, incluye el contenido de cada resultado.
        
    Returns:
        Dict: Resultados de la búsqueda.
    """
    return await get_docs(query, library, num_results, with_content)


async def mcp__get_docs_from_domain(
    query: str,
    domain: str,
    num_results: int = 5,
    with_content: bool = False
) -> Dict[str, Any]:
    """
    Herramienta MCP para buscar documentación para una consulta específica en un dominio personalizado.
    
    Args:
        query: Consulta de búsqueda.
        domain: Dominio específico para buscar.
        num_results: Número de resultados a devolver.
        with_content: Si es True, incluye el contenido de cada resultado.
        
    Returns:
        Dict: Resultados de la búsqueda.
    """
    return await get_docs_from_domain(query, domain, num_results, with_content)


async def mcp__search_web(
    query: str,
    site: Optional[str] = None,
    num_results: int = 10
) -> Dict[str, Any]:
    """
    Herramienta MCP para realizar una búsqueda en la web usando Google Serper API.
    
    Args:
        query: Consulta de búsqueda.
        site: Dominio específico para buscar.
        num_results: Número de resultados a devolver.
        
    Returns:
        Dict: Resultados de la búsqueda.
    """
    return await search_web(query, site, num_results)


async def mcp__fetch_url(
    url: str,
    timeout: int = 30
) -> Dict[str, str]:
    """
    Herramienta MCP para recuperar el contenido de una URL.
    
    Args:
        url: URL a recuperar.
        timeout: Tiempo máximo de espera en segundos.
        
    Returns:
        Dict: Título y contenido de la página.
    """
    return await fetch_url(url, timeout)


async def mcp__list_libraries() -> Dict[str, Any]:
    """
    Herramienta MCP para listar las bibliotecas soportadas.
    
    Returns:
        Dict: Lista de bibliotecas soportadas.
    """
    return {
        "libraries": list(docs_urls.keys()),
        "count": len(docs_urls)
    }


# Función principal para pruebas
async def main():
    """Función principal para pruebas."""
    # Ejemplo de uso
    query = "how to use async"
    library = "python"
    
    print(f"Buscando '{query}' en {library}...")
    
    # Callback para impresión
    async def print_callback(data, error=False):
        if error:
            print(f"ERROR: {data}")
        else:
            print(json.dumps(data, indent=2))
    
    try:
        result = await get_docs(
            query=query,
            library=library,
            num_results=3,
            with_content=True,
            stream_callback=print_callback
        )
        
        print("\nResultado final:")
        print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())