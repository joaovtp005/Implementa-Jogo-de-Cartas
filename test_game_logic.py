import pytest
from fastapi import HTTPException
from game import Game, draw_card_from_deck, storage  # Importamos o storage
from players import Player
from cards import Card

@pytest.fixture(autouse=True)
def clean_db():
    """Limpa o armazenamento antes de cada teste"""
    storage._games.clear() 
    storage._next_id = 0
    yield
    storage._games.clear()
    storage._next_id = 0


def test_comprar_carta_baralho_normal():
    """Testa a compra quando há cartas no deck."""
    carta_no_deck = Card(color="azul", value="1")
    game = Game(
        id_jogo=1,
        deck=[carta_no_deck],
        discard_pile=[]
    )
    
    card = draw_card_from_deck(game)
    
    assert card == carta_no_deck
    assert len(game.deck) == 0

def test_comprar_carta_reshuffle():
    """Testa se a pilha de descarte vira o novo deck quando o deck acaba."""
    carta_topo = Card(color="azul", value="9")
    carta_descarte_1 = Card(color="vermelho", value="2")
    carta_descarte_2 = Card(color="verde", value="3")
    
    game = Game(
        id_jogo=1,
        deck=[], 
        discard_pile=[carta_descarte_1, carta_descarte_2, carta_topo] 
    )
    
    nova_carta = draw_card_from_deck(game)

    assert len(game.discard_pile) == 1
    assert game.discard_pile[0] == carta_topo 
    assert len(game.deck) == 1 
    assert nova_carta in [carta_descarte_1, carta_descarte_2]

def test_empate_total():
    """Testa o erro quando não há cartas nem no deck nem no descarte."""
    game = Game(
        id_jogo=1,
        deck=[],
        discard_pile=[]
    )
    
    with pytest.raises(HTTPException) as excinfo:
        draw_card_from_deck(game)
    
    assert "O jogo empatou" in str(excinfo.value.detail)

def test_storage_get_game_valid():
    """Testa recuperar um jogo existente no storage."""
    game_instance = Game(id_jogo=5)
    storage.save_game(game_instance) 
    
    retrieved = storage.get_game(5)
    assert retrieved == game_instance

def test_storage_get_game_not_found():
    """Testa recuperar um jogo que não existe."""
    with pytest.raises(HTTPException) as excinfo:
        storage.get_game(999)
    assert excinfo.value.status_code == 404

def test_storage_get_game_finished():
    """Testa tentar recuperar um jogo finalizado."""
    game_instance = Game(id_jogo=5, game_over=True, winner=1)
    storage.save_game(game_instance)
    
    with pytest.raises(HTTPException) as excinfo:
        storage.get_game(5)
    assert excinfo.value.status_code == 400
    assert "já terminou" in str(excinfo.value.detail)