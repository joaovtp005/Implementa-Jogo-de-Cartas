# Implementação do Jogo - Engenharia de Software
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Uvicorn](https://img.shields.io/badge/Uvicorn-ASGI-4051B5?style=for-the-badge&logo=uvicorn&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-Tests-red?style=for-the-badge&logo=pytest&logoColor=white)


Projeto acadêmico de Back-end para um jogo de cartas estilo UNO, desenvolvido com **FastAPI**.
O objetivo principal deste projeto foi a aplicação prática de **Padrões de Projeto (Design Patterns)** de Engenharia de Software em um cenário real.

## 🛠️ Tecnologias Utilizadas

* [**Python 3.10+**](https://www.python.org/)
* [**FastAPI**](https://fastapi.tiangolo.com/): Para criação da API REST de alta performance.
* [**Uvicorn**](https://www.uvicorn.org/): Servidor ASGI para produção.
* [**Pytest**](https://docs.pytest.org/): Framework para testes automatizados.
* **Pydantic**: Para validação de dados e serialização.

## ✨ Funcionalidades

* **Preparação**: Iniciar jogo (2 a 10 jogadores), criar baralho e distribuir cartas.
* **Status do Jogo**: Consultar a mão do jogador, a carta da mesa e de quem é a vez.
* **Rodada**: Validar jogadas (Cor ou Valor) e alternar turnos.
* **Compra**: Sistema de comprar carta e passar a vez caso não tenha jogada.
* **Vitória**: Detecção automática de vencedor e bloqueio de partidas finalizadas.
* **Estatísticas**: Contagem de partidas iniciadas e finalizadas em tempo real.

## 🏗️ Padrões de Projeto Implementados

Este projeto implementa quatro padrões do GoF. Abaixo está a justificativa técnica para cada escolha no contexto deste jogo:

1. **Facade (`CardFacade`)**:
   * **Justificativa**: Centraliza a lógica de manipulação do baralho (criar, embaralhar, validar regras). Isso impede que o código da API precise lidar diretamente com a complexidade das listas de cartas.

2. **Observer (`GameObserver`)**:
   * **Justificativa**: Necessário para desacoplar a lógica do jogo da coleta de métricas. O jogo apenas "notifica" eventos, e o Observer cuida de contabilizar as partidas para a rota `/estatisticas`.

3. **Strategy (`CardStrategy`)**:
   * **Justificativa**: Permite que diferentes tipos de cartas tenham comportamentos distintos de execução. Embora o jogo atual use apenas regras normais, a arquitetura já está pronta para receber cartas especiais (como "Pular Vez") sem modificar o código principal.

4. **Command (`PlayCardCommand`, `PassTurnCommand`)**:
   * **Justificativa**: Encapsula as intenções do usuário como objetos. Isso organiza o código das rotas e facilita futuras implementações, como um histórico de jogadas ou funcionalidade de "desfazer".

## ⚙️ Como Executar Localmente

Siga os passos abaixo para rodar o projeto em sua máquina.

### 1. Clone o Repositório ou Baixe os Arquivos
Certifique-se de ter os arquivos `main.py` e `test_main.py` na mesma pasta.

### 2. Instale as Dependências
Abra o terminal na pasta do projeto e execute:

```bash
pip install fastapi "uvicorn[standard]" pytest httpx
```

### 3. Inicie o Servidor
Execute o comando abaixo para iniciar a API. O `--reload` reinicia o servidor automaticamente se houver alterações no código.

```bash
uvicorn main:app --reload
```

### 4. Acesse a Documentação Interativa
Abra seu navegador e acesse: **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**
Você verá a interface do Swagger UI onde pode testar todos os endpoints visualmente.

### 5. Execute os Testes Automatizados
Para garantir que todas as regras de negócio e padrões estão funcionando:

```bash
pytest -v
```

## 📚 Endpoints da API

Abaixo está o detalhamento das rotas principais disponíveis.

### 🏁 Preparação

* **`GET /novoJogo`**
    * **Descrição**: Inicia uma nova partida.
    * **Query Params**: `quantidadeJog` (int) - Entre 2 e 10.
    * **Retorno**: `{"id_jogo": int}`

### 🔍 Verificar Status

* **`GET /jogo/{id_jogo}/status`**
    * **Descrição**: Mostra a carta no topo da pilha de descarte e estatísticas da mesa.
* **`GET /jogo/{id_jogo}/{id_jogador}`**
    * **Descrição**: Retorna a mão (lista de cartas) do jogador especificado.
* **`GET /jogo/{id_jogo}/jogador_da_vez`**
    * **Descrição**: Informa o ID do jogador que deve jogar agora.

### 🎮 Rodada (Ações)

* **`PUT /jogo/{id_jogo}/jogar`**
    * **Descrição**: Joga uma carta da mão do jogador.
    * **Query Params**:
        * `id_jogador` (int)
        * `id_carta` (int) - O índice da carta na mão (0, 1, 2...).
* **`PUT /jogo/{id_jogo}/passa`**
    * **Descrição**: O jogador compra uma carta do baralho e passa a vez.
    * **Query Params**: `id_jogador` (int)

### 📊 Estatísticas

* **`GET /estatisticas`**
    * **Descrição**: Retorna quantas partidas foram iniciadas e finalizadas (via Observer).

## 📂 Estrutura do Projeto

```text
📦 JogoDeCartas
 ┣ 📜 main.py          # Lógica Principal, Modelos e Rotas
 ┣ 📜 test_main.py     # Testes Unitários e de Integração
 ┗ 📜 README.md        # Documentação do Projeto
