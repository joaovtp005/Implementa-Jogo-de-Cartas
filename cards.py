import random
from enum import Enum
from pydantic import BaseModel
from typing import List

class Color(str, Enum):
    RED = "vermelho"
    BLUE = "azul"
    GREEN = "verde"
    YELLOW = "amarelo"

class Value(str, Enum):
    ZERO = "0"
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"
    SIX = "6"
    SEVEN = "7"
    EIGHT = "8"
    NINE = "9"

class Card(BaseModel):
    color: Color
    value: Value
    
    def __str__(self):
        return f"{self.color.value} {self.value.value}"

def create_deck() -> List[Card]:
    """Cria um baralho completo e o embaralha."""
    deck = []
    
    for color in Color:
        deck.append(Card(color=color, value=Value.ZERO))
    
    for _ in range(2):
        for color in Color:
            for value in [v for v in Value if v != Value.ZERO]:
                deck.append(Card(color=color, value=value))
    
    random.shuffle(deck)
    return deck