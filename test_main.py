import pytest
from fastapi.testclient import TestClient
from main import app, games_db, observer, Card, Game, Player, card_facade
import main  

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_client():
    """
    Um fixture que reseta o estado do 'banco de dados' em memória
    e do observer antes de cada teste ser executado.
    """
    # Limpa o estado antes do teste
    games_db.clear()
    observer.partidas_iniciadas = 0
    observer.partidas_finalizadas = 0
    
    
    main.next_game_id = 0 
    
    yield 

    # Limpa o estado depois do teste 
    games_db.clear()
    observer.partidas_iniciadas = 0
    observer.partidas_finalizadas = 0
    main.next_game_id = 0


# Testes dos Endpoints Principais

def test_novo_jogo_sucesso():
    """Testa a criação de um novo jogo com 2 jogadores."""
    response = client.get("/novoJogo?quantidadeJog=2")
    assert response.status_code == 201
    data = response.json()
    assert data["id_jogo"] == 0
    
    # Verifica se o jogo foi realmente criado no DB
    assert 0 in games_db
    game = games_db[0]
    assert len(game.players) == 2
    assert len(game.players[0].hand) == 5 
    assert len(game.players[1].hand) == 5
    
    
    
    assert len(game.deck) == 76 - 1 - 10 
    
    assert len(game.discard_pile) == 1
    assert observer.partidas_iniciadas == 1

def test_novo_jogo_falha_jogadores():
    """Testa os limites de jogadores (mínimo 2, máximo 10)."""
    # Teste abaixo do limite
    response_min = client.get("/novoJogo?quantidadeJog=1")
    assert response_min.status_code == 422 
    
    # Teste acima do limite
    response_max = client.get("/novoJogo?quantidadeJog=11")
    assert response_max.status_code == 422

def test_estatisticas():
    """Testa se o observer está contando corretamente."""
    response = client.get("/estatisticas")
    assert response.status_code == 200
    assert response.json() == {"partidas_iniciadas": 0, "partidas_finalizadas": 0}

    client.get("/novoJogo?quantidadeJog=2")
    client.get("/novoJogo?quantidadeJog=3")
    
    response = client.get("/estatisticas")
    assert response.status_code == 200
    assert response.json() == {"partidas_iniciadas": 2, "partidas_finalizadas": 0}

# Testes de Fluxo de Jogo

def test_status_do_jogo():
    """Testa o endpoint de status."""
    client.get("/novoJogo?quantidadeJog=3")
    
    response = client.get("/jogo/0/status")
    assert response.status_code == 200
    data = response.json()
    assert data["jogador_da_vez"] == 0
    assert data["cartas_por_jogador"] == {"jogador_0": 5, "jogador_1": 5, "jogador_2": 5}
    assert "color" in data["carta_no_topo"]
    assert "value" in data["carta_no_topo"]

def test_status_jogo_inexistente():
    response = client.get("/jogo/99/status")
    assert response.status_code == 404
    assert response.json()["detail"] == "Jogo não encontrado"

def test_jogador_da_vez():
    client.get("/novoJogo?quantidadeJog=2")
    response = client.get("/jogo/0/jogador_da_vez")
    assert response.status_code == 200
    assert response.json() == {"jogador_da_vez": 0}

def test_ver_cartas():
    client.get("/novoJogo?quantidadeJog=2")
    response = client.get("/jogo/0/0") # Jogo 0, Jogador 0
    assert response.status_code == 200
    data = response.json()
    assert "hand" in data
    assert len(data["hand"]) == 5

def test_ver_cartas_jogador_inexistente():
    client.get("/novoJogo?quantidadeJog=2")
    response = client.get("/jogo/0/99") # Jogo 0, Jogador 99
    assert response.status_code == 404
    
    
    assert response.json()["detail"] == "Jogador não encontrado"

# Testes de Ações (PUT) - com Mock

def test_jogar_carta_sucesso(monkeypatch):
    """Testa uma jogada válida."""
    top_card = Card(color="azul", value="5")
    valid_card = Card(color="azul", value="1")
    player_hand = [Card(color="vermelho", value="2"), valid_card]
    
    game = Game(
        id_jogo=0,
        players=[Player(id=0, hand=player_hand), Player(id=1, hand=[])],
        deck=[],
        discard_pile=[top_card],
        current_player_id=0
    )
    monkeypatch.setitem(games_db, 0, game)
    
    response = client.put("/jogo/0/jogar?id_jogador=0&id_carta=1") 
    
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Jogada válida. Próximo jogador: 1"
    assert data["proximo_jogador"] == 1
    
    
    assert data["carta_jogada"] == valid_card.model_dump()
    
    assert game.current_player_id == 1 
    assert valid_card not in game.players[0].hand 
    assert game.discard_pile[-1] == valid_card 

def test_jogar_carta_nao_e_a_vez():
    """Testa tentar jogar fora da vez."""
    client.get("/novoJogo?quantidadeJog=2") 
    
    response = client.put("/jogo/0/jogar?id_jogador=1&id_carta=0")
    assert response.status_code == 403
    assert "Não é a vez do jogador 1" in response.json()["detail"]

def test_jogar_carta_invalida_regras(monkeypatch):
    """Testa jogar uma carta que não combina (cor/valor)."""
    top_card = Card(color="azul", value="5")
    invalid_card = Card(color="vermelho", value="1") 
    
    game = Game(
        id_jogo=0,
        players=[Player(id=0, hand=[invalid_card])],
        discard_pile=[top_card],
        current_player_id=0
    )
    monkeypatch.setitem(games_db, 0, game)
    
    response = client.put("/jogo/0/jogar?id_jogador=0&id_carta=0")
    
    assert response.status_code == 400
    assert "A carta não combina em cor ou valor" in response.json()["detail"]

def test_jogar_carta_indice_invalido():
    """Testa jogar uma carta com índice fora do range da mão."""
    client.get("/novoJogo?quantidadeJog=2") # Mão tem 5 cartas (índices 0-4)
    response = client.put("/jogo/0/jogar?id_jogador=0&id_carta=99")
    
    assert response.status_code == 400
    assert "Índice de carta inválido" in response.json()["detail"]

def test_passar_a_vez():
    """Testa se o jogador compra uma carta e passa a vez."""
    client.get("/novoJogo?quantidadeJog=2")
    game = games_db[0] 
    
    cartas_antes = len(game.players[0].hand)
    deck_antes = len(game.deck)
    
    response = client.put("/jogo/0/passa?id_jogador=0")
    
    assert response.status_code == 200
    data = response.json()
    assert data["proximo_jogador"] == 1
    assert "nova_carta_comprada" in data
    
    assert game.current_player_id == 1 
    assert len(game.players[0].hand) == cartas_antes + 1 
    assert len(game.deck) == deck_antes - 1 

def test_passar_a_vez_nao_e_a_vez():
    client.get("/novoJogo?quantidadeJog=2")
    
    response = client.put("/jogo/0/passa?id_jogador=1")
    assert response.status_code == 403
    assert "Não é a vez do jogador 1" in response.json()["detail"]

def test_vitoria_e_jogo_terminado(monkeypatch):
    """Testa uma jogada que leva à vitória e o bloqueio do jogo."""
    top_card = Card(color="azul", value="5")
    win_card = Card(color="azul", value="1")
    
    game = Game(
        id_jogo=0,
        players=[Player(id=0, hand=[win_card]), Player(id=1, hand=[])],
        discard_pile=[top_card],
        current_player_id=0
    )
    monkeypatch.setitem(games_db, 0, game)
    
    response_win = client.put("/jogo/0/jogar?id_jogador=0&id_carta=0")
    
    assert response_win.status_code == 200
    assert "VENCEU O JOGO" in response_win.json()["message"]
    
    assert game.game_over == True
    assert game.winner == 0
    assert observer.partidas_finalizadas == 1 
    
    response_after = client.put("/jogo/0/jogar?id_jogador=1&id_carta=0")
    assert response_after.status_code == 400
    assert "O jogo 0 já terminou" in response_after.json()["detail"]
    
    response_status = client.get("/jogo/0/status")
    assert response_status.status_code == 400

    assert "O jogo 0 já terminou" in response_status.json()["detail"]
