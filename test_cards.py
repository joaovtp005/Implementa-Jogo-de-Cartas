import pytest
from cards import Card, create_deck, COLORS, VALUES

def test_modelo_carta():
    """Testa se a criação de uma única carta funciona."""
    card = Card(color="azul", value="5")
    assert card.color == "azul"
    assert card.value == "5"

def test_tamanho_baralho():
    """
    Testa se o baralho é criado com o número correto de cartas.
    Regra atual: 
    - 4 zeros (1 por cor)
    - 2 cópias de 1-9 para cada cor (2 * 9 * 4 = 72)
    Total esperado: 76 cartas.
    """
    deck = create_deck()
    assert len(deck) == 76

def test_distribuicao_cores():
    """Testa se temos cartas de todas as cores."""
    deck = create_deck()
    cores_no_baralho = set(card.color for card in deck)
    
    # Verifica se todas as cores constantes estão no baralho
    for color in COLORS:
        assert color in cores_no_baralho

def test_baralho_embaralhado():
    """
    Testa se o baralho não está ordenado (probabilístico).
    Gera dois baralhos e verifica se a ordem é diferente.
    """
    deck1 = create_deck()
    deck2 = create_deck()

    assert deck1 != deck2