import pytest
from fastapi.testclient import TestClient
from main import app 
from game import Game, Player, games_db
from cards import Card

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_cleanup():
    """
    Limpa o banco de dados antes e depois de cada teste.
    Garante que um teste não interfira no outro.
    """
    games_db.clear()
    # Reinicia o contador de IDs se necessário (opcional, dependendo da implementação)
    import main
    import game
    game.next_game_id = 0
    yield
    games_db.clear()

# --- 1. Testes de Criação de Jogo (/novoJogo) ---

def test_criar_jogo_sucesso():
    """Verifica se cria o jogo e retorna 201 Created."""
    response = client.get("/novoJogo?quantidadeJog=4")
    assert response.status_code == 201
    
    data = response.json()
    assert "id_jogo" in data
    assert isinstance(data["id_jogo"], int)
    
    # Verifica efeito colateral (se o jogo foi salvo)
    assert 0 in games_db
    assert len(games_db[0].players) == 4

def test_validacao_jogadores_minimo():
    """FastAPI deve retornar 422 se tentarmos criar jogo com 1 jogador."""
    response = client.get("/novoJogo?quantidadeJog=1")
    assert response.status_code == 422

def test_validacao_jogadores_maximo():
    """FastAPI deve retornar 422 se tentarmos criar jogo com 11 jogadores."""
    response = client.get("/novoJogo?quantidadeJog=11")
    assert response.status_code == 422

def test_validacao_tipo_dado():
    """FastAPI deve retornar 422 se enviarmos texto em vez de número."""
    response = client.get("/novoJogo?quantidadeJog=dois")
    assert response.status_code == 422

# --- 2. Testes de Leitura de Estado (/jogo/{id}/...) ---

def test_ler_status_jogo_inexistente():
    """Deve retornar 404 se o ID do jogo não existe."""
    response = client.get("/jogo/999/status")
    assert response.status_code == 404
    assert response.json()["detail"] == "Jogo não encontrado"

def test_ler_mao_jogador():
    """Cria um jogo manualmente e tenta ler a mão do jogador."""
    # Setup manual do estado (Mock)
    game = Game(id_jogo=10, players=[Player(id=0, hand=[Card(color="azul", value="1")])])
    games_db[10] = game
    
    response = client.get("/jogo/10/0") # Jogo 10, Jogador 0
    assert response.status_code == 200
    assert len(response.json()["hand"]) == 1
    assert response.json()["hand"][0]["color"] == "azul"

def test_ler_mao_jogador_invalido():
    """Jogo existe, mas jogador não."""
    game = Game(id_jogo=10, players=[Player(id=0)])
    games_db[10] = game
    
    response = client.get("/jogo/10/5") # Jogador 5 não existe
    assert response.status_code == 404

# --- 3. Testes de Ações de Jogo (/jogar, /passa) ---

def test_jogar_carta_fora_de_vez():
    """Tenta jogar com o jogador 1 quando é a vez do jogador 0."""
    game = Game(
        id_jogo=1, 
        current_player_id=0, 
        players=[Player(id=0), Player(id=1)],
        discard_pile=[Card(color="verde", value="0")]
    )
    games_db[1] = game
    
    response = client.put("/jogo/1/jogar?id_jogador=1&id_carta=0")
    assert response.status_code == 403
    assert "Não é a vez" in response.json()["detail"]

def test_jogar_carta_indice_invalido():
    """Tenta jogar a carta de índice 10 quando só tem 1 carta."""
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[Card(color="azul", value="1")])],
        discard_pile=[Card(color="azul", value="2")]
    )
    games_db[1] = game
    
    response = client.put("/jogo/1/jogar?id_jogador=0&id_carta=10")
    assert response.status_code == 400
    assert "Índice de carta inválido" in response.json()["detail"]

def test_jogar_carta_regra_invalida():
    """Tenta jogar Vermelho em cima de Azul (sem combinar número)."""
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[Card(color="vermelho", value="1")])],
        discard_pile=[Card(color="azul", value="9")]
    )
    games_db[1] = game
    
    response = client.put("/jogo/1/jogar?id_jogador=0&id_carta=0")
    assert response.status_code == 400
    assert "Jogada inválida" in response.json()["detail"]

def test_jogar_carta_vitoria():
    """Verifica se ao jogar a última carta, o jogo detecta vitória."""
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[Card(color="azul", value="5")])], # Apenas 1 carta
        discard_pile=[Card(color="azul", value="9")]
    )
    games_db[1] = game
    
    response = client.put("/jogo/1/jogar?id_jogador=0&id_carta=0")
    
    assert response.status_code == 200
    assert "VENCEU" in response.json()["message"]
    # Verifica estado interno
    assert games_db[1].game_over is True
    assert games_db[1].winner == 0

def test_passar_vez_sucesso():
    """Verifica se comprar carta funciona e passa a vez."""
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[]), Player(id=1)],
        deck=[Card(color="amarelo", value="1")],
        discard_pile=[Card(color="verde", value="2")]
    )
    games_db[1] = game
    
    response = client.put("/jogo/1/passa?id_jogador=0")
    
    assert response.status_code == 200
    data = response.json()
    assert "nova_carta_comprada" in data
    assert data["nova_carta_comprada"]["color"] == "amarelo"
    
    # Verifica se passou a vez
    assert games_db[1].current_player_id == 1