#!/bin/bash

# Cores para logs
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}===> Iniciando GetJobs IA Service <===${NC}"

# Garante que o diretório atual está no PYTHONPATH para evitar erros de import
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Verifica se o arquivo .env existe
if [ ! -f .env ]; then
    echo "⚠️  Aviso: Arquivo .env não encontrado. Usando configurações padrão."
fi

# Inicia o serviço principal via Uvicorn
# O main.py já inicia o gRPC (porta 50051) e o Worker do BullMQ em background
echo -e "${GREEN}===> Iniciando FastAPI na porta 8000 (gRPC na 50051)...${NC}"
python app/main.py
