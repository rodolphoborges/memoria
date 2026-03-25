# Guia Técnico: ERP TOTVS Protheus com SQL Server

## 1. Visão Geral do TOTVS Protheus

O TOTVS Protheus é um ERP (Enterprise Resource Planning) amplamente utilizado no mercado brasileiro.
Ele é desenvolvido em AdvPL (Advanced Protheus Language) e roda sobre um Application Server chamado TOTVS Application Server (TAS).
O sistema suporta múltiplos bancos de dados, sendo os mais comuns: SQL Server, Oracle e PostgreSQL.

## 2. Estrutura de Banco de Dados

### Tabelas principais

- **SA1** - Cadastro de Clientes
- **SA2** - Cadastro de Fornecedores
- **SB1** - Cadastro de Produtos
- **SC5** - Cabeçalho de Pedidos de Venda
- **SC6** - Itens de Pedidos de Venda
- **SF2** - Cabeçalho de Notas Fiscais de Saída
- **SD2** - Itens de Notas Fiscais de Saída
- **SE2** - Contas a Pagar
- **SE1** - Contas a Receber

### Campos obrigatórios (padrão Protheus)

Toda tabela do Protheus possui os campos de controle:
- `XX_FILIAL` — filial da empresa
- `XX_COD` ou `XX_NUM` — chave primária do registro
- `D_E_L_E_T_` — flag de exclusão lógica (`*` = deletado, ` ` = ativo)
- `R_E_C_N_O_` — número do registro físico (rowid interno)

## 3. Queries SQL Mais Comuns

### Consultar clientes ativos

```sql
SELECT A1_COD, A1_NOME, A1_CGC, A1_TEL
FROM SA1010
WHERE A1_FILIAL = '01'
  AND D_E_L_E_T_ = ' '
ORDER BY A1_NOME
```

### Pedidos de venda em aberto

```sql
SELECT C5_NUM, C5_CLIENTE, C5_EMISSAO, C5_TOTAL
FROM SC5010
WHERE C5_FILIAL = '01'
  AND C5_LOTVEND = ' '
  AND D_E_L_E_T_ = ' '
ORDER BY C5_EMISSAO DESC
```

### Saldo de estoque por produto

```sql
SELECT B1_COD, B1_DESC, B2_QATU, B2_CM1
FROM SB1010
INNER JOIN SB2010 ON B2_COD = B1_COD AND B2_FILIAL = B1_FILIAL
WHERE B1_FILIAL = '01'
  AND D_E_L_E_T_ = ' '
  AND B2_QATU > 0
```

## 4. Configuração do Ambiente

### Arquivo de configuração (appserver.ini)

```ini
[General]
Maxstringsize=10
consolelog=1

[Drivers]
Active=MSSQL

[MSSQL]
Driver=MSSQL2008
Server=SEU_SERVIDOR_SQL
Database=PROTHEUS12
Alias=PROTHEUS12
```

### Conexão via ODBC com Python

```python
import pyodbc

conn = pyodbc.connect(
    'DRIVER={SQL Server};'
    'SERVER=seu_servidor;'
    'DATABASE=PROTHEUS12;'
    'UID=usuario;'
    'PWD=senha'
)
cursor = conn.cursor()
cursor.execute("SELECT TOP 10 A1_COD, A1_NOME FROM SA1010 WHERE D_E_L_E_T_ = ' '")
for row in cursor.fetchall():
    print(row)
```

## 5. Boas Práticas

- Sempre filtrar por `D_E_L_E_T_ = ' '` para excluir registros deletados logicamente.
- Nunca usar `DELETE` direto em tabelas do Protheus — use exclusão via sistema.
- Índices customizados devem ser criados com prefixo `IX_` para não conflitar com índices do sistema.
- Monitorar o tamanho do campo `R_E_C_N_O_` em tabelas muito grandes (limite de INT no SQL Server).

## 6. Erros Frequentes e Soluções

| Erro | Causa | Solução |
|------|-------|---------|
| `Table not found SA1010` | Filial com sufixo diferente | Verificar o sufixo correto da empresa/filial |
| `Deadlock detected` | Concorrência em tabelas de movimento | Implementar retry logic na aplicação |
| `String truncation` | Campo maior que o tamanho definido no SX3 | Ajustar tamanho no dicionário de dados |
| `Login timeout` | Configuração de pool no appserver.ini | Aumentar `MaxConn` no appserver.ini |