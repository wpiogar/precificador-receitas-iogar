# ============================================================================
# DOCKERFILE - FRONTEND FOOD COST SYSTEM
# ============================================================================
# Descrição: Container React/Vite com Nginx para produção
# Base: Node.js 20 Alpine (build) + Nginx Alpine (runtime)
# Data: 25/11/2025
# Autor: Will - Empresa: IOGAR
# ============================================================================

# ============================================================================
# STAGE 1: BUILD - Compilar aplicação React/Vite
# ============================================================================
FROM node:20-alpine AS build

# Instalar dependências do sistema necessárias para build
RUN apk add --no-cache \
    python3 \
    make \
    g++

# Diretório de trabalho
WORKDIR /app

# Copiar arquivos de dependências primeiro (para cache do Docker)
COPY package.json package-lock.json* ./

# Instalar dependências do Node.js
# Usar npm ci para instalação limpa e reproduzível (se package-lock existe)
# Caso contrário, usar npm install
RUN if [ -f package-lock.json ]; then \
        npm ci --legacy-peer-deps; \
    else \
        npm install --legacy-peer-deps; \
    fi

# Copiar código fonte da aplicação
COPY . .

# Argumentos de build para variáveis de ambiente Vite
ARG VITE_API_URL=http://localhost:8000
ARG VITE_ENVIRONMENT=production

# Definir variáveis de ambiente para o build
ENV VITE_API_URL=${VITE_API_URL}
ENV VITE_ENVIRONMENT=${VITE_ENVIRONMENT}
ENV GENERATE_SOURCEMAP=false

# Executar build de produção
RUN npm run build

# Verificar se build foi bem-sucedido
RUN if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then \
        echo "ERRO: Build falhou - dist/index.html não encontrado!"; \
        exit 1; \
    fi

# ============================================================================
# STAGE 2: RUNTIME - Nginx para servir aplicação
# ============================================================================
FROM nginx:alpine

# Instalar curl para health check
RUN apk add --no-cache curl

# Remover configuração padrão do Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Copiar configuração customizada do Nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar arquivos build do stage anterior
COPY --from=build /app/dist /usr/share/nginx/html

# Criar usuário não-root para Nginx
RUN addgroup -g 101 -S nginx && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx 2>/dev/null || true

# Ajustar permissões
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    chown -R nginx:nginx /etc/nginx/conf.d && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

# Mudar para usuário não-root
USER nginx

# Expor porta HTTP
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Comando de inicialização
CMD ["nginx", "-g", "daemon off;"]

# ============================================================================
# NOTAS DE USO
# ============================================================================
# Build com variáveis de ambiente:
# docker build \
#   --build-arg VITE_API_URL=https://api.exemplo.com \
#   --build-arg VITE_ENVIRONMENT=production \
#   -t foodcost-frontend .
#
# Run:
# docker run -p 80:80 foodcost-frontend
# ============================================================================