# TROUBLESHOOTING - Importação de Insumos com Códigos Duplicados

## Problema Identificado

**Sintoma**: Importação de insumos falha com erro `duplicate key value violates unique constraint "ix_insumos_codigo"` mesmo após limpar o banco de dados do restaurante.

**Causa Raiz**: Índice UNIQUE global incorreto na tabela `insumos` que impede códigos duplicados entre restaurantes diferentes.

---

## Diagnóstico Rápido

### 1. Verificar o Problema

Conecte ao banco de produção:

```bash
psql postgresql://[CONNECTION_STRING]
```

Execute:

```sql
-- Verificar se existe o índice problemático
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'insumos' 
AND indexname = 'ix_insumos_codigo';
```

**Resultado esperado se houver problema:**
```sql
ix_insumos_codigo | CREATE UNIQUE INDEX ix_insumos_codigo ON public.insumos USING btree (codigo)
```

### 2. Confirmar Constraints Corretas

```sql
-- Verificar constraints no código
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'insumos'::regclass 
AND conname LIKE '%codigo%';
```

**Resultado esperado (CORRETO):**
```sql
uq_insumo_restaurante_codigo | u | UNIQUE (restaurante_id, codigo)
```

### 3. Testar Inserção Manual

```sql
-- Verificar se código existe em outros restaurantes
SELECT codigo, restaurante_id, nome
FROM insumos 
WHERE codigo IN ('5000', '5003', '5002');

-- Tentar inserir manualmente no seu restaurante
INSERT INTO insumos (
    restaurante_id, codigo, nome, quantidade, unidade, preco_compra, 
    fator, eh_fornecedor_anonimo, grupo, subgrupo
) VALUES (
    23, '5000', 'TESTE', 1.0, 'kg', 100, 1.0, true, '', ''
);
```

**Se der erro `ix_insumos_codigo`** → Problema confirmado!

---

## Solução

### Passo 1: Remover Índice Incorreto

```sql
-- Se houver transação aberta, feche primeiro
ROLLBACK;

-- Remover o índice problemático
DROP INDEX ix_insumos_codigo;
```

### Passo 2: Verificar Remoção

```sql
-- Confirmar que o índice foi removido
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'insumos' 
AND indexname = 'ix_insumos_codigo';
```

**Resultado esperado:** 0 rows (nenhum índice encontrado)

### Passo 3: Testar Importação

1. Acesse o sistema web
2. Faça upload da planilha de insumos
3. Confirme a importação

**Resultado esperado:**
- ✅ Todos os insumos únicos são importados
- ✅ Apenas duplicados no mesmo restaurante são ignorados
- ✅ Códigos podem existir em restaurantes diferentes

---

## Prevenção Futura

### Migration para Garantir Índice Correto

Crie uma migration no Alembic para garantir que esse problema não ocorra novamente:

**Arquivo**: `backend/alembic/versions/XXXX_fix_insumos_codigo_index.py`

```python
"""fix: remover índice global incorreto de código de insumos

Revision ID: fix_insumos_codigo_index
Revises: [revision anterior]
Create Date: 2025-12-04

"""
from alembic import op

revision = 'fix_insumos_codigo_index'
down_revision = '[revision anterior]'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Remove índice UNIQUE global incorreto no campo 'codigo'.
    
    O índice ix_insumos_codigo impedia códigos duplicados entre restaurantes,
    mas o comportamento correto é permitir o mesmo código em restaurantes
    diferentes (garantido pela constraint uq_insumo_restaurante_codigo).
    """
    print("🔧 Removendo índice global incorreto ix_insumos_codigo...")
    
    # Remover índice se existir
    op.drop_index('ix_insumos_codigo', table_name='insumos', if_exists=True)
    
    print("✅ Índice removido - códigos podem ser duplicados entre restaurantes")


def downgrade() -> None:
    """
    Não recriar o índice incorreto no downgrade.
    O índice global era um bug, não uma feature.
    """
    print("⚠️  Downgrade: não recriando índice incorreto")
    pass
```

### Verificação em Todos os Ambientes

Execute em **staging**, **QA** e **produção**:

```sql
-- Verificar se índice existe
SELECT indexname 
FROM pg_indexes 
WHERE tablename = 'insumos' 
AND indexname = 'ix_insumos_codigo';

-- Se existir, remover
DROP INDEX IF EXISTS ix_insumos_codigo;
```

---

## Comportamento Esperado do Sistema

### Regras de Códigos de Insumos

1. **Mesmo código em restaurantes diferentes**: ✅ PERMITIDO
   - Restaurante A pode ter insumo código 5000
   - Restaurante B pode ter insumo código 5000
   - São insumos completamente independentes

2. **Código duplicado no mesmo restaurante**: ❌ PROIBIDO
   - Garantido pela constraint `uq_insumo_restaurante_codigo`
   - Sistema ignora linhas duplicadas durante importação

3. **Insumos globais (sem restaurante_id)**: ⚠️ CUIDADO
   - Não devem existir em produção
   - Se existirem, podem causar conflitos

### Verificação de Saúde do Sistema

Execute periodicamente:

```sql
-- Verificar insumos sem restaurante (não deveria existir)
SELECT COUNT(*) FROM insumos WHERE restaurante_id IS NULL;

-- Verificar duplicados dentro do mesmo restaurante
SELECT restaurante_id, codigo, COUNT(*) as duplicados
FROM insumos
GROUP BY restaurante_id, codigo
HAVING COUNT(*) > 1;

-- Verificar índices na tabela insumos
SELECT indexname, indexdef 
FROM pg_indexes 
WHERE tablename = 'insumos'
ORDER BY indexname;
```

**Resultados esperados:**
- 0 insumos sem restaurante_id
- 0 duplicados no mesmo restaurante
- Apenas índices corretos (sem ix_insumos_codigo)

---

## Contexto Técnico

### Por Que o Problema Ocorreu?

1. **Migration antiga incorreta**: Alguma migration criou o índice `ix_insumos_codigo` como UNIQUE global
2. **Ambiente inconsistente**: O índice só existia em produção, não em staging/local
3. **Constraints duplicadas**: Duas constraints conflitantes:
   - ✅ `uq_insumo_restaurante_codigo` (CORRETO)
   - ❌ `ix_insumos_codigo` (INCORRETO - sobrescreve o correto)

### Por Que Staging/Local Funcionavam?

O índice incorreto `ix_insumos_codigo` não foi criado em staging/local:
- Pode ter sido uma migration manual em produção
- Ou migration executada apenas em produção em data anterior
- Ou diferença nas versões de migration entre ambientes

### Estrutura Correta da Tabela Insumos

```sql
-- Constraint CORRETA (permite duplicação entre restaurantes)
CONSTRAINT uq_insumo_restaurante_codigo UNIQUE (restaurante_id, codigo)

-- Índices recomendados
CREATE INDEX idx_insumos_restaurante ON insumos(restaurante_id);
CREATE INDEX idx_insumos_codigo ON insumos(codigo);  -- NÃO UNIQUE!
```

---

## Checklist de Troubleshooting

Quando encontrar problemas de importação:

- [ ] Verificar logs de erro no sistema
- [ ] Conectar no banco de dados
- [ ] Verificar índices na tabela insumos
- [ ] Verificar constraints na tabela insumos
- [ ] Testar inserção manual com código existente em outro restaurante
- [ ] Verificar se há insumos sem restaurante_id
- [ ] Comparar estrutura entre staging e produção
- [ ] Verificar versão das migrations (alembic_version)
- [ ] Limpar dados de teste e testar novamente

---

## Comandos Úteis

### Acessar Banco de Produção

```bash
# Via psql
psql postgresql://[CONNECTION_STRING]

# Via Docker (se não tiver psql instalado)
docker run -it --rm postgres:14 psql postgresql://[CONNECTION_STRING]
```

### Verificação Rápida de Saúde

```sql
-- Copie e cole tudo de uma vez
SELECT 
    'Total de insumos' as metrica,
    COUNT(*)::text as valor
FROM insumos
UNION ALL
SELECT 
    'Insumos sem restaurante',
    COUNT(*)::text
FROM insumos 
WHERE restaurante_id IS NULL
UNION ALL
SELECT 
    'Restaurantes com insumos',
    COUNT(DISTINCT restaurante_id)::text
FROM insumos
UNION ALL
SELECT 
    'Índice global incorreto',
    CASE WHEN EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'insumos' 
        AND indexname = 'ix_insumos_codigo'
    ) THEN '⚠️ EXISTE (PROBLEMA!)' 
    ELSE '✅ Não existe (OK)' 
    END;
```

---

## Contato e Suporte

**Desenvolvedor**: Will - IOGAR  
**Data do Fix**: 04/12/2025  
**Versão do Sistema**: Food Cost System v1.0

**Para questões:**
1. Verifique este documento primeiro
2. Execute os comandos de diagnóstico
3. Se o problema persistir, documente:
   - Mensagem de erro completa
   - Resultado das queries de diagnóstico
   - Ambiente afetado (staging/produção)
   - Passos para reproduzir

---

## Histórico de Mudanças

| Data | Versão | Mudanças |
|------|--------|----------|
| 04/12/2025 | 1.0 | Documento inicial - Fix do índice ix_insumos_codigo |

---

**✅ Problema resolvido com sucesso em 04/12/2025**  
**🎉 337 de 435 insumos importados após correção (77% de sucesso)**
