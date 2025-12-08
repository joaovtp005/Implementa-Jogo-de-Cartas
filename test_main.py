import pytest
from fastapi.testclient import TestClient
from main import app
from game import Game, Player, storage # Importa o storage
from cards import Card

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_cleanup():
    """Limpa o GameStorage antes e depois dos testes."""
    storage._games.clear()
    storage._next_id = 0
    yield
    storage._games.clear()


def test_criar_jogo_sucesso():
    response = client.get("/novoJogo?quantidadeJog=4")
    assert response.status_code == 201
    
    data = response.json()
    assert "id_jogo" in data
    id_novo = data["id_jogo"]
    
    assert id_novo in storage.games_db
    assert len(storage.games_db[id_novo].players) == 4

def test_validacao_jogadores():

    response = client.get("/novoJogo?quantidadeJog=1")
    assert response.status_code == 422

    response = client.get("/novoJogo?quantidadeJog=11")
    assert response.status_code == 422

def test_ler_status_jogo_inexistente():
    response = client.get("/jogo/999/status")
    assert response.status_code == 404

def test_ler_mao_jogador():

    game = Game(id_jogo=10, players=[Player(id=0, hand=[Card(color="azul", value="1")])])
    storage.save_game(game)
    
    response = client.get("/jogo/10/0")
    assert response.status_code == 200
    assert response.json()["hand"][0]["color"] == "azul"

def test_jogar_carta_fora_de_vez():
    game = Game(
        id_jogo=1, 
        current_player_id=0, 
        players=[Player(id=0), Player(id=1)],
        discard_pile=[Card(color="verde", value="0")]
    )
    storage.save_game(game)
    
    response = client.put("/jogo/1/jogar?id_jogador=1&id_carta=0")
    assert response.status_code == 403

def test_jogar_carta_sucesso():
    """Testa uma jogada válida completa (sem vencer o jogo)."""
    top_card = Card(color="azul", value="5")
    valid_card = Card(color="azul", value="1")
    extra_card = Card(color="vermelho", value="9")
    
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[valid_card, extra_card]), Player(id=1)],
        discard_pile=[top_card]
    )
    storage.save_game(game)
    
    response = client.put("/jogo/1/jogar?id_jogador=0&id_carta=0")
    
    assert response.status_code == 200

    assert response.json()["proximo_jogador"] == 1

    game_salvo = storage.get_game(1)
    assert len(game_salvo.players[0].hand) == 1 
    assert game_salvo.discard_pile[-1] == valid_card


def test_jogar_carta_vitoria():
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[Card(color="azul", value="5")])], 
        discard_pile=[Card(color="azul", value="9")]
    )
    storage.save_game(game)
    
    response = client.put("/jogo/1/jogar?id_jogador=0&id_carta=0")
    
    assert response.status_code == 200
    assert "VENCEU" in response.json()["message"]
    
    assert storage.games_db[1].game_over is True

def test_passar_vez_sucesso():
    game = Game(
        id_jogo=1,
        current_player_id=0,
        players=[Player(id=0, hand=[]), Player(id=1)],
        deck=[Card(color="amarelo", value="1")],
        discard_pile=[Card(color="verde", value="2")]
    )
    storage.save_game(game)
    
    response = client.put("/jogo/1/passa?id_jogador=0")
    
    assert response.status_code == 200
    assert "nova_carta_comprada" in response.json()
    assert storage.games_db[1].current_player_id == 1