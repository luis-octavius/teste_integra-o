# ANS Analytics Frontend
Este é o frontend para o projeto ANS Analytics, uma aplicação web para visualizar e analisar dados de operadoras de saúde no Brasil, com base nos dados públicos da Agência Nacional de Saúde Suplementar (ANS).

## Funcionalidades
-   Listagem e busca de operadoras de saúde por Razão Social, UF e modalidade.
-   Visualização de detalhes de cada operadora, incluindo suas despesas.
-   Dashboard com estatísticas gerais do setor (total de operadoras, despesas, etc.).
-   Gráficos interativos para análise de distribuição de despesas por estado (UF).

## Tecnologias Utilizadas

-   **[Vue.js 3](https://vuejs.org/)**: Um framework progressivo para construir interfaces de usuário.
-   **[Vite](https://vitejs.dev/)**: Um build tool moderno e rápido para desenvolvimento web.
-   **[Pinia](https://pinia.vuejs.org/)**: A loja de estado (state management) para aplicações Vue.js.
-   **[Vue Router](https://router.vuejs.org/)**: Para o roteamento da aplicação.
-   **[Chart.js](https://www.chartjs.org/)**: Para a renderização dos gráficos de estatísticas.
-   **[Axios](https://axios-http.com/)**: Para as requisições à API backend.
-   **[PrimeVue](https://primevue.org/)**: Biblioteca de componentes de UI.

## Estrutura do Projeto
```
├───.gitignore
├───index.html
├───package-lock.json
├───package.json
├───vite.config.js
├───node_modules/...
└───src/
├───App.vue
├───main.js
├───components/ # Componentes Vue reutilizáveis
├───composables/ # Funções de composição (hooks)
├───router/ # Configuração das rotas (Vue Router)
├───services/ # Lógica de comunicação com a API
├───stores/ # Módulos da store (Pinia)
└───views/ # Componentes de página (rotas)
```

## Pré-requisitos
-   [Node.js](https://nodejs.org/) (versão 18.x ou superior)
-   [npm](https://www.npmjs.com/) ou um gerenciador de pacotes compatível.

## Instalação e Execução
1.  **Clone o repositório e acesse a pasta:**

```bash
git clone https://github.com/luis-octavius/teste_intuitivecare.git
cd test_intuitive_care/frontend
```

2.  **Instale as dependências:**

Com npm:
```bash
npm install
```

3.  **Configure o Backend**
Certifique-se de que o servidor backend esteja em execução.
Por padrão, a aplicação frontend tentará se conectar a um backend em `http://localhost:8000`. Esta URL pode ser configurada no arquivo `src/services/api.js`.

5.  **Execute o servidor de desenvolvimento:**

A aplicação frontend iniciará em `http://localhost:5173` (ou outra porta, caso a 5173 esteja em uso).

```bash
npm run dev
```

## Scripts Disponíveis

-   `npm run dev`: Inicia o servidor de desenvolvimento com Hot-Reload.
-   `npm run build`: Compila a aplicação para produção.
-   `npm run preview`: Inicia um servidor local para visualizar a build de produção.

## Trade-offs


### 4.2.2. ESTRATÉGIA DE PAGINAÇÃO: OFFSET-BASED
Opção escolhida: Offset-based pagination
Motivos:
1. Volume de dados: Espera-se até 10.000 operadoras → offset funciona bem
2. Frequência de atualizações: Dados cadastrais mudam pouco
3. Simplicidade: Fácil implementação e entendimento
4. Compatibilidade: Funciona com qualquer ordenação
        
Alternativas consideradas:
- Cursor-based: Melhor para milhões de registros ou dados muito dinâmicos
- Keyset: Complexo para implementar, benefício pequeno neste caso
        
Com offset-based, o usuário pode navegar diretamente para qualquer página.

### 4.3.2. GERENCIAMENTO DE ESTADO: PINIA
Opção escolhida: Pinia (Vue 3)
Motivos:
1. Oficial para Vue 3: Sucessor do Vuex
2. TypeScript friendly: Melhor tipagem
3. Simplicidade: Menos boilerplate que Vuex
4. Modular: Stores independentes
5. DevTools: Integração com Vue DevTools

Para esta aplicação:
- Complexidade moderada: Múltiplas views compartilham estado
- Dados de API: Cache local de operadoras
- Estados de UI: Loading, erros, filtros

Alternativas:
- Props/Events: Muito complexo para compartilhamento global
- Composables: Bom para lógica, mas não para estado compartilhado

### 4.3.3. PERFORMANCE DA TABELA: Virtual Scrolling
Opção escolhida: Virtual Scrolling (v-show + computed)
    
Motivos:
1. Volume de dados: Até 10.000 operadoras
2. UX: Rola suavemente sem travar
3. Performance: Renderiza apenas elementos visíveis
4. Simplicidade: Implementação nativa

Alternativas:
- Paginação no frontend: Já temos no backend
- Infinite scroll: Complexo para tabelas
- Lazy loading: Bom para imagens, não tabelas
    
Implementação:
- Mostra apenas 50 linhas por vez
- Calcula posição baseada no scroll

### 4.3.4. TRATAMENTO DE ERROS E LOADING
Abordagem: Mensagens específicas + estados claros
Motivos:
1. UX: Usuário sabe exatamente o que aconteceu
2. Debugging: Facilita identificar problemas
3. Profissionalismo: Interface polida

Estados tratados:
1. Loading: Spinner + texto
2. Vazio: Mensagem amigável
3. Erro: Mensagem específica + ação
4. Sucesso: Conteúdo normal

    
