# 🚀 Guia de Deploy - Food Cost System

Documentação completa para deploy do sistema no Render.

---

## 📋 Ambientes

O sistema possui 2 ambientes no Render:

| Ambiente | Branch | URL Frontend | URL Backend |
|----------|--------|--------------|-------------|
| **Staging** | `staging` | https://food-cost-frontend-staging.onrender.com | https://food-cost-backend-staging.onrender.com |
| **Production** | `main` | https://food-cost-frontend.onrender.com | https://food-cost-backend.onrender.com |

---

## 🔧 Pré-requisitos

Antes de fazer deploy, certifique-se de:

- ✅ Código testado localmente com Docker
- ✅ Todas as mudanças commitadas
- ✅ Branch correta (staging ou main)
- ✅ Acesso ao dashboard do Render

---

## 🎯 Deploy para Staging

### **Método 1: Script Automático (Recomendado)**
```powershell
# Executar script de deploy
.\deploy-staging.ps1
```

### **Método 2: Manual**
```powershell
# 1. Mudar para branch staging
git checkout staging

# 2. Merge das mudanças (se necessário)
git merge develop

# 3. Push para Render
git push origin staging
```

### **Pós-Deploy:**

1. Aguardar build completar no Render (~5-10 minutos)
2. Verificar logs no dashboard
3. Testar aplicação em staging
4. Se tudo OK, pode fazer deploy em produção

---

## 🏭 Deploy para Production

### **Método 1: Script Automático (Recomendado)**
```powershell
# Executar script de deploy
.\deploy-production.ps1
```

O script irá:
- Verificar se está na branch `main`
- Verificar se há mudanças não commitadas
- Solicitar confirmação (digite "PRODUÇÃO")
- Fazer push para Render

### **Método 2: Manual**
```powershell
# 1. Mudar para branch main
git checkout main

# 2. Merge do staging (após testar)
git merge staging

# 3. Push para Render
git push origin main
```

---

## 🔍 Monitoramento

### **Acompanhar Deploy**

1. Acesse: https://dashboard.render.com
2. Selecione o serviço (backend ou frontend)
3. Aba "Events" mostra progresso do deploy
4. Aba "Logs" mostra logs em tempo real

### **Verificar Health**
```powershell
# Backend health check
curl https://food-cost-backend.onrender.com/api/v1/health

# Frontend (deve retornar HTML)
curl https://food-cost-frontend.onrender.com
```

---

## 🐛 Troubleshooting

### **Build Failed**

1. Verificar logs no Render
2. Testar build localmente: `docker-compose build`
3. Verificar `render.yaml` está correto
4. Verificar variáveis de ambiente no Render

### **Migrations Failed**
```bash
# Conectar ao shell do backend no Render
# (via dashboard > Shell)

# Rodar migrations manualmente
alembic upgrade head
```

### **Frontend não carrega**

1. Verificar se build gerou arquivos em `dist/`
2. Verificar `VITE_API_URL` está correto
3. Limpar cache do navegador
4. Verificar routes no `render.yaml`

### **CORS Error**

1. Verificar `ALLOWED_ORIGINS` no backend
2. Adicionar URL do frontend se necessário
3. Reiniciar serviço backend

---

## 🔐 Variáveis de Ambiente

### **Backend (Render Dashboard)**

Configurar em: Dashboard > Service > Environment
```
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=<gerado automaticamente>
DATABASE_URL=<do PostgreSQL Render>
ALLOWED_ORIGINS=https://food-cost-frontend.onrender.com,https://food-cost-frontend-staging.onrender.com
```

### **Frontend (render.yaml)**

Já configuradas no `render.yaml`:
```yaml
VITE_API_URL=https://food-cost-backend.onrender.com
VITE_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

---

## 📊 Checklist de Deploy

### **Antes do Deploy**

- [ ] Código testado localmente
- [ ] Testes passando
- [ ] Migrations testadas
- [ ] Docker funcionando
- [ ] Commit com mensagem clara
- [ ] Branch correta

### **Durante o Deploy**

- [ ] Build iniciou sem erros
- [ ] Migrations rodaram com sucesso
- [ ] Logs sem erros críticos
- [ ] Health check OK

### **Após o Deploy**

- [ ] Login funciona
- [ ] APIs respondendo
- [ ] Frontend carregando
- [ ] CORS funcionando
- [ ] Features principais OK
- [ ] Performance aceitável

---

## 🔄 Rollback

Se algo der errado em produção:
```powershell
# 1. Reverter último commit
git revert HEAD

# 2. Push para main
git push origin main

# Ou redeployer commit anterior no dashboard do Render
```

---

## 📞 Suporte

**Desenvolvedor:** Will - IOGAR  
**Última Atualização:** 25/11/2025

Para problemas, verificar:
1. Logs do Render
2. Documentação deste arquivo
3. Issues no GitHub