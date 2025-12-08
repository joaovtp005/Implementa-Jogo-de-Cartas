import random
from pydantic import BaseModel
from typing import List

# Cores e valores constantes
COLORS = ['vermelho', 'azul', 'verde', 'amarelo']
VALUES = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

class Card(BaseModel):
    color: str
    value: str

def create_deck() -> List[Card]:
    """Cria um baralho completo e o embaralha."""
    deck = []
    
    for color in COLORS:
        deck.append(Card(color=color, value='0'))
    
    for _ in range(2):
        for color in COLORS:
            for value in VALUES[1:]:
                deck.append(Card(color=color, value=value))
    
    random.shuffle(deck)
    return deck