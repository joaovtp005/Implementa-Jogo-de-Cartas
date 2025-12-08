import random
from typing import List, Optional, Dict
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from cards import Card
from players import Player

class Game(BaseModel):
    id_jogo: int
    players: List[Player] = Field(default_factory=list)
    deck: List[Card] = Field(default_factory=list)
    discard_pile: List[Card] = Field(default_factory=list)
    current_player_id: int = 0
    game_over: bool = False
    winner: Optional[int] = None


class GameStorage:
    """Armazenamento simples sem variáveis globais"""
    def __init__(self):
        self._games = {}
        self._next_id = 0
    
    @property
    def games_db(self):
        return self._games
    
    @property
    def next_game_id(self):
        current = self._next_id
        self._next_id += 1
        return current
    
    def get_game(self, id_jogo: int) -> Game:
        """Busca um jogo ou lança erro 404"""
        game = self._games.get(id_jogo)
        if not game:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogo não encontrado")
        if game.game_over:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"O jogo {id_jogo} já terminou. Vencedor: Jogador {game.winner}"
            )
        return game
    
    def save_game(self, game: Game) -> None:
        """Salva um jogo no armazenamento"""
        self._games[game.id_jogo] = game
        
    def update_game_state(self, game: Game) -> None:
        """Atualiza o estado de um jogo no armazenamento"""
        self._games[game.id_jogo] = game

storage = GameStorage()

# --- Funções Lógicas ---

def draw_card_from_deck(game: Game) -> Card:
    """Compra uma carta do baralho, reembaralhando a pilha de descarte se necessário."""
    if not game.deck:
        if not game.discard_pile:
             raise HTTPException(status_code=500, detail="O jogo empatou! Não há mais cartas para comprar.")

        top_card = game.discard_pile.pop()
        game.deck = game.discard_pile
        random.shuffle(game.deck)
        game.discard_pile = [top_card]
        
        if not game.deck:
             raise HTTPException(status_code=500, detail="O jogo empatou! Não há mais cartas para comprar.")
             
    return game.deck.pop()