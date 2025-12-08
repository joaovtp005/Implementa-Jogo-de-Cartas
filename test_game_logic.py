import pytest
from fastapi import HTTPException
from game import Game, draw_card_from_deck, get_game, games_db
from players import Player
from cards import Card

# Fixture para limpar o DB antes de cada teste deste arquivo
@pytest.fixture(autouse=True)
def clean_db():
    games_db.clear()
    yield
    games_db.clear()

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
    """
    Testa se a pilha de descarte vira o novo deck quando o deck acaba.
    Esta é uma regra complexa e crítica do jogo.
    """
    carta_topo = Card(color="azul", value="9")
    carta_descarte_1 = Card(color="vermelho", value="2")
    carta_descarte_2 = Card(color="verde", value="3")
    
    game = Game(
        id_jogo=1,
        deck=[], # Deck vazio
        # Pilha de descarte tem o topo (que fica) e as outras (que viram deck)
        discard_pile=[carta_descarte_1, carta_descarte_2, carta_topo] 
    )
    
    # Ao comprar, o jogo deve:
    # 1. Manter 'carta_topo' no descarte.
    # 2. Mover carta_descarte_1 e 2 para o deck e embaralhar.
    # 3. Retirar uma carta do novo deck e retornar.
    
    nova_carta = draw_card_from_deck(game)
    
    # Verificações
    assert len(game.discard_pile) == 1
    assert game.discard_pile[0] == carta_topo # A carta do topo não deve ser movida
    assert len(game.deck) == 1 # Eram 2 no descarte, 1 foi comprada, sobrou 1
    
    # A carta comprada deve ser uma das que estavam no descarte (exceto o topo)
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

def test_get_game_valid():
    """Testa recuperar um jogo existente."""
    game_instance = Game(id_jogo=5)
    games_db[5] = game_instance
    
    retrieved = get_game(5)
    assert retrieved == game_instance

def test_get_game_not_found():
    """Testa recuperar um jogo que não existe."""
    with pytest.raises(HTTPException) as excinfo:
        get_game(999)
    assert excinfo.value.status_code == 404

def test_get_game_finished():
    """Testa tentar recuperar um jogo que já acabou."""
    game_instance = Game(id_jogo=5, game_over=True, winner=1)
    games_db[5] = game_instance
    
    with pytest.raises(HTTPException) as excinfo:
        get_game(5)
    assert excinfo.value.status_code == 400
    assert "já terminou" in str(excinfo.value.detail)