from pydantic import BaseModel, Field
from typing import List
from cards import Card  

class Player(BaseModel):
    id: int
    hand: List[Card] = Field(default_factory=list)