# ANS API

## Pré-requisitos
Antes de começar, certifique-se de ter:

1. **PostgreSQL** instalado e rodando
2. **Python 3.9+** instalado
3. **UV** instalado (gerenciador de pacotes Python)
4. Ter executado o script [csv_script](../csv_script) para gerar os dados

## Instalação
1. Copie os arquivos csv:
```bash
# Da pasta raiz da api, execute o seguinte comando
cp -r `../csv_script/csv ./csv/
```

2. Execute o script SQL:
```bash
psql -U postgres -f scripts/script.sql
```

3. Ative o uv:
**Linux/Mac**:
```bash
uv sync
```

**Windows (Powershell)**
```
.venv\Scripts\Activate.ps1
```

4. Crie o `.env` e coloque a URL da database corretamente:
```bash
cp .env.example .env
```

5. Rode o import para o banco de dados:
```bash
uv run scripts/import_data.py
```

6. Rode a API com uvicorn:
```bash
uv run uvicorn app.main:app --reload
```

A API estará disponível em `http://localhost:8000`

## Trade-offs

### SQL
#### 3.2. ESTRUTURAÇÃO DAS TABELAS

**Normalização Escolhida: Modelo Híbrido (Estrela)**
- **Tabela de Dimensão**: `cadastro_operadoras` (dados mestres)
- **Tabela de Fatos**: `despesas_consolidadas` (transacional)
- **Tabela de Agregação**: `despesas_agregadas` (pré-calculado)

**Justificativa:**
- **Volume**: Dados transacionais são grandes, agregados são menores
- **Atualizações**: Separar permite atualizações em batch sem bloquear consultas
- **Consultas**: Agregada para dashboards, detalhada para análises profundas

**Tipos de Dados:**
- **Monetários**: `DECIMAL(15,2)` - Precisão exata para cálculos financeiros
- **Datas**: `DATE` para referência, `TIMESTAMP` para auditoria
- **Textos**: `VARCHAR` com tamanhos apropriados, `utf8mb4` para acentos

### 3.3. IMPORT E TRATAMENTO DE DADOS

**Problemas Encontrados e Soluções:**

1. **Valores NULL em obrigatórios**: Remoção dos registros
2. **Strings em campos numéricos**: Regex para extrair apenas números
3. **Datas inconsistentes**:

### API
#### 4.2.1. Escolha do Framework
Opção escolhida: FastAPI

Justificativa:
- Performance: Baseado em async/await, mais rápido que Flask para APIs REST
- Validação automática: Pydantic integrado para schemas type-safe
- Documentação: Swagger UI e ReDoc gerados automaticamente
- Modernidade: Suporte nativo a async/await e type hints
- Manutenibilidade: Código mais limpo e organizado

#### 4.2.2. Estratégia de Paginação

Opção escolhida: **Offset-based pagination**

Justificativa:
- Volume de dados: Até 10.000 operadoras - offset funciona bem
- Frequência de atualizações: Dados cadastrais mudam pouco
- Simplicidade: Fácil implementação e entendimento
- Navegação direta: Usuário pode ir para qualquer página
- Compatibilidade: Funciona com qualquer ordenação

#### 4.2.3. Cache vs Queries Diretas

Opção escolhida: **Cache Redis + cálculos sob demanda**

Justificativa:
- Frequência de atualização: Dados mudam trimestralmente
- Consistência: Cache de 10 minutos é suficiente para análises
- Performance: Evita cálculos pesados repetidos
- Escalabilidade: Redis pode ser clusterizado se necessário
- Simplicidade: Implementação com decorator @cache

#### 4.2.4. Estrutura de Resposta da API

Opção escolhida: **Dados + Metadados completos**

Justificativa:
- Frontend amigável: Cliente tem todas as informações necessárias
- Padrão REST: Segue boas práticas para APIs paginadas
- Performance: Evita queries extras para metadados
- Experiência do usuário: Interface pode mostrar totais e navegação
- Manutenibilidade: Estrutura consistente em todas as respostas

#### 4.3.1. Estratégia de Busca/Filtro

Opção escolhida: Híbrida (servidor + debounce no cliente)

Justificativa:
- Volume de dados: Busca no servidor para dados completos
- Performance: Debounce evita chamadas excessivas à API
- Experiência do usuário: Feedback imediato durante digitação
- Cobertura: Filtros simples no cliente, complexos no servidor
- Flexibilidade: Balance entre responsividade e precisão
