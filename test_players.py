from players import Player
from cards import Card

def test_criar_jogador():
    """Testa a inicialização básica de um jogador."""
    player = Player(id=10)
    assert player.id == 10
    assert player.hand == [] 

def test_jogador_receber_cartas():
    """Testa adicionar cartas manualmente à mão do jogador."""
    player = Player(id=1)
    card = Card(color="verde", value="2")
    
    player.hand.append(card)
    
    assert len(player.hand) == 1
    assert player.hand[0].color == "verde"