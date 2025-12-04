import random
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

#  1. Modelos de Dados (Pydantic) 
# Define a estrutura de uma carta
class Card(BaseModel):
    color: str
    value: str

# Define a estrutura de um jogador
class Player(BaseModel):
    id: int
    hand: List[Card] = Field(default_factory=list)

# Define a estrutura completa de um Jogo
class Game(BaseModel):
    id_jogo: int
    players: List[Player] = Field(default_factory=list)
    deck: List[Card] = Field(default_factory=list)
    discard_pile: List[Card] = Field(default_factory=list)
    current_player_id: int = 0
    game_over: bool = False
    winner: Optional[int] = None

# 2. Lógica do Jogo (Funções Auxiliares) 

# Cores e valores
COLORS = ['vermelho', 'azul', 'verde', 'amarelo']
VALUES = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']

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

def draw_card_from_deck(game: Game) -> Card:
    """Compra uma carta do baralho, reembaralhando a pilha de descarte se necessário."""
    if not game.deck:
       
        top_card = game.discard_pile.pop()
        game.deck = game.discard_pile
        random.shuffle(game.deck)
        
        game.discard_pile = [top_card]
        
        
        if not game.deck:
             raise HTTPException(status_code=500, detail="O jogo empatou! Não há mais cartas para comprar.")
             
    return game.deck.pop()

#  3. O "Banco de Dados" em Memória 

app = FastAPI(title="API de Jogo de Cartas")


games_db: Dict[int, Game] = {}
next_game_id: int = 0

def get_game(id_jogo: int) -> Game:
    """Função auxiliar para buscar um jogo ou lançar um erro 404."""
    game = games_db.get(id_jogo)
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogo não encontrado")
    if game.game_over:
         raise HTTPException(
             status_code=status.HTTP_400_BAD_REQUEST, 
             detail=f"O jogo {id_jogo} já terminou. Vencedor: Jogador {game.winner}"
         )
    return game

#  4. Endpoints da API (Rotas) 

#Parte 1: Preparação

@app.get("/novoJogo", status_code=status.HTTP_201_CREATED)
def novo_jogo(quantidadeJog: int = Query(..., ge=2, le=10)):
    """
    Inicia um novo jogo para 'quantidadeJog' jogadores.
    Distribui 5 cartas para cada e retorna o ID do jogo.
    """
    global next_game_id
    game_id = next_game_id
    next_game_id += 1
    
    # 1. Cria o jogo
    new_deck = create_deck()
    players = [Player(id=i) for i in range(quantidadeJog)]
    
    new_game = Game(
        id_jogo=game_id,
        players=players,
        deck=new_deck,
        current_player_id=0  
    )
    
    # 2. Distribuir 5 cartas
    for _ in range(5):
        for player in new_game.players:
            player.hand.append(draw_card_from_deck(new_game))
            
    
    new_game.discard_pile.append(draw_card_from_deck(new_game))
    
    
    games_db[game_id] = new_game
    
    
    return {"id_jogo": game_id}

# Parte 2: Verificar Status do Jogo

@app.get("/jogo/{id_jogo}/status")
def status_do_jogo(id_jogo: int):
    """
    (Endpoint Bônus) Mostra o estado atual da mesa.
    """
    game = get_game(id_jogo)
    return {
        "jogador_da_vez": game.current_player_id,
        "carta_no_topo": game.discard_pile[-1],
        "cartas_por_jogador": {f"jogador_{p.id}": len(p.hand) for p in game.players}
    }




@app.get("/jogo/{id_jogo}/jogador_da_vez")
def jogador_da_vez(id_jogo: int):
    """
    Retorna o ID do jogador da vez.
    """
    game = get_game(id_jogo)
    # 1. Retorna o ID do jogador da vez
    return {"jogador_da_vez": game.current_player_id}


@app.get("/jogo/{id_jogo}/{id_jogador}")
def ver_cartas(id_jogo: int, id_jogador: int):
    """
    Mostra as cartas atuais na mão de um jogador específico.
    """
    game = get_game(id_jogo)
    
    if id_jogador < 0 or id_jogador >= len(game.players):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogador não encontrado")
        
    
    return {"hand": game.players[id_jogador].hand}



# Parte 3: Rodada

@app.put("/jogo/{id_jogo}/jogar")
def jogar_carta(id_jogo: int, id_jogador: int, id_carta: int = Query(..., ge=0)):
    """
    Joga uma carta (pelo índice dela na mão) se for a vez do jogador
    e a carta for válida.
    """
    game = get_game(id_jogo)
    
    
    if id_jogador != game.current_player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Não é a vez do jogador {id_jogador}. É a vez do jogador {game.current_player_id}."
        )
        
    player = game.players[id_jogador]
    
    
    if id_carta < 0 or id_carta >= len(player.hand):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Índice de carta inválido.")
        
    card_to_play = player.hand[id_carta]
    top_card = game.discard_pile[-1]
    
    if card_to_play.color == top_card.color or card_to_play.value == top_card.value:
        
        played_card = player.hand.pop(id_carta)
        game.discard_pile.append(played_card)
        
        
        if not player.hand:
            game.game_over = True
            game.winner = id_jogador
            return {"message": f"Jogador {id_jogador} VENCEU O JOGO!"}
            
        
        game.current_player_id = (game.current_player_id + 1) % len(game.players)
        
        return {
            "message": f"Jogada válida. Próximo jogador: {game.current_player_id}",
            "carta_jogada": played_card
        }
    else:
       
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jogada inválida: A carta não combina em cor ou valor com a carta do topo."
        )

@app.put("/jogo/{id_jogo}/passa")
def passar_a_vez(id_jogo: int, id_jogador: int):
    """
    O jogador compra uma carta e passa a vez.
    """
    game = get_game(id_jogo)
    
    
    if id_jogador != game.current_player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Não é a vez do jogador {id_jogador}. É a vez do jogador {game.current_player_id}."
        )
        
    
    new_card = draw_card_from_deck(game)
    game.players[id_jogador].hand.append(new_card)
    
    game.current_player_id = (game.current_player_id + 1) % len(game.players)
    
    return {
        "message": f"Você comprou uma carta. Próximo jogador: {game.current_player_id}",
        "nova_carta_comprada": new_card

    }

