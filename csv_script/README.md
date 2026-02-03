# CSV Script 

Esse script em Python executa os seguintes passos:  
  
1 - Acessa à [API da ANS](https://dadosabertos.ans.gov.br/FTP/PDA/).  
2 - Identifica as **Demonstrações Contábeis** dos últimos três trimestres.    
3 - Baixa os arquivos, cada um relativo a um trimestre, que estão na extensão `.zip` e os extrai automaticamente.   
4 - Organiza e mescla os dados dos três arquivos em um só.  
5 - Filtra os dados negativos e zerados.   
6 - Compacta o CSV mesclado para `.zip`.   
7 - Faz um join entre os **[Dados Cadastrais das Operadoras Ativas](https://dadosabertos.ans.gov.br/FTP/PDA/operadoras_de_plano_de_saude_ativas/)** usando como chave o `REGISTRO_ANS`.  
8 - Une as despesas de cada registro que contém o mesmo `cnpj` e cria um csv ordenado do valor maior para o menor em um arquivi chamado `despesas_agregadas.csv`

## Pré-requisitos

- Python 3.9 ou superior
- **UV** instalado

## Instalando o UV

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux/Mac:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Executando o projeto
1. Clonar o repositório

```bash
git clone https://github.com/luis-octavius/teste_intuitivecare.git
cd teste_intuitivecare/csv_script/
```

2. Criar ambiente virtual e instalar dependências
```bash
# Criar ambiente virtual e instalar dependências automaticamente
uv sync
```

3. Ativar o ambiente virtual

Windows (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

Linux/Mac:
```bash
source .venv/bin/activate
```

4. Execute:
```
uv run main.py
```

## Trade-offs

### 1.2. Processamento de Arquivos
> Trade-off técnico: Decida entre processar todos os arquivos em memória de uma vez
ou processar incrementalmente. Documente sua escolha e justifique considerando o
volume de dados.

Escolhi processar todos os arquivos de uma vez, dado que, mesmo que o arquivos tenham bastante dados, são apenas três. Além disso, considero a premissa de que o hardware disponível para a execução do aplicativo é suficiente
para tal.

### 2.1. Validação de Dados com Estratégias Diferentes
> Trade-off técnico: Para CNPJs inválidos, você precisará decidir como tratá-los. Considere diferentes estratégias e escolha a que fizer mais sentido. Escolha uma
abordagem, implemente-a e documente no README sua escolha e os prós/contras considerados.

Não há o campo `CNPJ` nos arquivos baixados, somente o `Registro_ANS`, portanto, essa parte deixo para responder no próximo ponto.

### 2.2. Enriquecimento de Dados com Tratamento de Falhas
> Trade-off técnico: Para o join, você precisará decidir como processar os dados. Considere diferentes estratégias de processamento e escolha a que fizer mais sentido para o seu contexto. Documente sua escolha e justifique baseado no tamanho estimado dos dados e nas características do problema.

Uma vez que nos arquivos iniciais dos trimestres que criaram um único CSV onde o campo `cnpj` estava ausente, por isso, decidi fazer o join por meio do `Registro_ANS` com o `cnpj` que está no arquivo CSV de Dados Cadastrais das Operadoras ativas, como pedido. Só fiz esse ajuste pela ausência do CNPJ no primeiro passo, mas resolvi dessa forma. 

### 2.3. Agregação com Múltiplas Estratégias
> Trade-off técnico: Para ordenação, você precisará escolher uma estratégia considerando o volume de dados e os recursos disponíveis. Justifique sua escolha no
README.

A agregação ocorre em agrupamentos sequenciais múltiplos. Uma vantagem é que o código fica mais fácil de ser lido.
Uma desvantagem é que os dados são processados múltiplas vezes com operações `groupby`. Como disse anteriormente, o programa é pensado
para ser executado em bom hardware, portanto, não há nenhum defícit em suas operações. Por ser mais legível, a manutenção do código é, inclusive, uma porta
de entrada para a refatoração e melhora de performance no futuro. 
O que poderia ser feito, por exemplo, seria uma agregação única, com todas as operações sendo feitas de uma só vez.
