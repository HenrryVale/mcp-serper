# MCP-Serper

MCP-Serper es una herramienta que permite buscar documentación técnica en línea a través de Google Serper y exponerla mediante la interfaz de MCP (Model Context Protocol). Esta herramienta facilita el acceso a documentación técnica actualizada desde diversas fuentes.

## Características

- 🔍 Búsqueda de documentación en bibliotecas predefinidas (OpenAI, LangChain, Llama-Index, etc.)
- 🌐 Soporte para búsqueda en dominios personalizados
- 📡 Implementación de Server-Sent Events (SSE) para streaming de resultados en tiempo real
- 🚀 Interfaz web de demostración para probar la funcionalidad
- 🔒 Validación de dominios para prevenir abusos
- 🐳 Containerización con Docker para facilitar el despliegue

## Requisitos

- Python 3.9+
- Docker y Docker Compose (para la ejecución containerizada)
- API Key de Google Serper (obtener en [serper.dev](https://serper.dev))

## Instalación

### Usando Docker (recomendado)

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/mcp-serper.git
   cd mcp-serper
   ```

2. Crea un archivo `.env` a partir del ejemplo:
   ```bash
   cp .env.example .env
   ```

3. Edita el archivo `.env` y añade tu API Key de Google Serper:
   ```
   SERPER_API_KEY=tu_api_key_aqui
   ```

4. Construye y ejecuta los contenedores:
   ```bash
   docker-compose up -d
   ```

5. Accede a la interfaz de demostración en [http://localhost:8080](http://localhost:8080)

### Instalación manual

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/mcp-serper.git
   cd mcp-serper
   ```

2. Crea un entorno virtual y actívalo:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Crea un archivo `.env` a partir del ejemplo:
   ```bash
   cp .env.example .env
   ```

5. Edita el archivo `.env` y añade tu API Key de Google Serper:
   ```
   SERPER_API_KEY=tu_api_key_aqui
   ```

6. Ejecuta el servidor:
   ```bash
   python server.py
   ```

7. Para la interfaz de demostración, puedes usar un servidor web como Nginx o simplemente ejecutar un servidor Python:
   ```bash
   # Desde el directorio demo
   cd demo
   python -m http.server 8080
   ```

## Uso

### API REST

El servidor expone las siguientes rutas para su uso como API REST:

- `GET /health` - Verificar el estado del servidor
- `GET /sse` - Endpoint para establecer conexión SSE
- `POST /messages/get_docs_stream` - Buscar documentación en bibliotecas predefinidas
- `POST /messages/get_docs_from_domain_stream` - Buscar documentación en un dominio personalizado
- `POST /cancel` - Cancelar una operación en curso

### Cliente de demostración

El cliente de demostración proporciona una interfaz web sencilla para probar la funcionalidad de MCP-Serper:

1. Accede a [http://localhost:8080](http://localhost:8080)
2. Selecciona una biblioteca o introduce un dominio personalizado
3. Escribe tu consulta de búsqueda
4. Haz clic en "Buscar" para iniciar la búsqueda
5. Los resultados se mostrarán en tiempo real a medida que se obtienen

### Ejemplos de uso con curl

#### Buscar documentación en una biblioteca predefinida:
```bash
curl -X POST http://localhost:8000/messages/get_docs_stream \
  -H "Content-Type: application/json" \
  -d '{"query": "embeddings", "library": "langchain"}'
```

#### Buscar documentación en un dominio personalizado:
```bash
curl -X POST http://localhost:8000/messages/get_docs_from_domain_stream \
  -H "Content-Type: application/json" \
  -d '{"query": "asyncio", "domain": "docs.python.org"}'
```

#### Establecer conexión SSE para recibir eventos:
```bash
curl -N http://localhost:8000/sse
```

## Estructura del Proyecto

```
mcp-serper/
├── demo/                  # Cliente de demostración
│   ├── index.html         # Interfaz web
│   └── nginx.conf         # Configuración de Nginx
├── .env.example           # Plantilla para variables de entorno
├── docker-compose.yml     # Configuración de Docker Compose
├── Dockerfile             # Definición de la imagen Docker
├── mcp_serper.py          # Módulo principal de herramientas MCP
├── pyproject.toml         # Configuración del proyecto
├── README.md              # Documentación
├── requirements.txt       # Dependencias
└── server.py              # Servidor Starlette con soporte SSE
```

## Arquitectura

El proyecto sigue una arquitectura basada en eventos con los siguientes componentes:

1. **Capa de API**: Implementada con Starlette, expone endpoints REST y SSE.
2. **Capa de Herramientas MCP**: Implementa las funciones para búsqueda y extracción de documentación.
3. **Cliente SSE**: Interfaz web que se conecta al servidor para recibir eventos en tiempo real.
4. **Redis**: (Opcional) Para implementación futura de caché de resultados.

## Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Empuja a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la licencia MIT. Ver `LICENSE` para más detalles.

## Contacto

Henrry Vale - email@ejemplo.com

URL del Proyecto: [https://github.com/HenrryVale/mcp-serper](https://github.com/HenrryVale/mcp-serper)