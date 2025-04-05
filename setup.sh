#!/bin/bash

# Script de configuración inicial para MCP-Serper
echo "=== Configuración de MCP-Serper ==="
echo

# Verificar dependencias
echo "Verificando dependencias..."
command -v python3 >/dev/null 2>&1 || { echo "Error: Python 3 no está instalado. Por favor, instálelo."; exit 1; }
command -v pip3 >/dev/null 2>&1 || { echo "Error: pip3 no está instalado. Por favor, instálelo."; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "Advertencia: Docker no está instalado. No podrá usar los contenedores."; }
command -v docker-compose >/dev/null 2>&1 || { echo "Advertencia: Docker Compose no está instalado. No podrá usar docker-compose."; }

# Crear entorno virtual
echo "Creando entorno virtual..."
python3 -m venv venv
source venv/bin/activate || { echo "Error: No se pudo activar el entorno virtual."; exit 1; }

# Instalar dependencias
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Configurar archivo .env
if [ ! -f .env ]; then
    echo "Configurando archivo .env..."
    cp .env.example .env
    
    # Solicitar la clave API de Serper
    echo
    echo "Necesitas una clave API de Google Serper para usar esta herramienta."
    echo "Puedes obtener una en https://serper.dev/"
    echo
    read -p "Ingresa tu clave API de Serper: " serper_key
    
    # Actualizar .env con la clave proporcionada
    if [ ! -z "$serper_key" ]; then
        # En Linux/Mac
        if [[ "$OSTYPE" == "darwin"* || "$OSTYPE" == "linux-gnu"* ]]; then
            sed -i "" "s/your_serper_api_key_here/$serper_key/" .env 2>/dev/null || sed -i "s/your_serper_api_key_here/$serper_key/" .env
        # En Windows con Git Bash
        else
            sed -i "s/your_serper_api_key_here/$serper_key/" .env
        fi
        echo "Clave API configurada correctamente."
    else
        echo "No se proporcionó clave API. Tendrás que editar el archivo .env manualmente."
    fi
else
    echo "Archivo .env ya existe."
fi

# Crear directorios necesarios
echo "Creando directorios necesarios..."
mkdir -p logs
mkdir -p demo

# Verificar que el cliente demo existe
if [ ! -f demo/index.html ]; then
    echo "Creando archivos de demostración..."
    
    # Crear directorio demo si no existe
    mkdir -p demo
    
    # Crear archivo de configuración de Nginx para demo
    cat > demo/nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location /api/ {
        proxy_pass http://mcp-serper:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Configuración para SSE
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
    }
}
EOF
fi

echo
echo "=== Configuración completada ==="
echo
echo "Para iniciar el servicio, ejecuta:"
echo "  docker-compose up -d"
echo
echo "Para probar el servicio sin Docker:"
echo "  python server.py"
echo
echo "La API estará disponible en: http://localhost:8000"
echo "El cliente de demostración estará disponible en: http://localhost:8080"
echo