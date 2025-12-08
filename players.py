from pydantic import BaseModel, Field
from typing import List
from cards import Card  # Importando a classe Card do arquivo cards.py

class Player(BaseModel):
    id: int
    hand: List[Card] = Field(default_factory=list)