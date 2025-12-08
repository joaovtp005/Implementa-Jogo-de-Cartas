from fastapi import FastAPI, HTTPException, status, Query
from cards import create_deck
from players import Player
import game 

app = FastAPI(title="API de Jogo de Cartas")
INITIAL_HAND_SIZE = 5

@app.get("/novoJogo", status_code=status.HTTP_201_CREATED)
def novo_jogo(quantidadeJog: int = Query(..., ge=2, le=10)):
    """
    Inicia um novo jogo para 'quantidadeJog' jogadores.
    Distribui 5 cartas para cada e retorna o ID do jogo.
    """
    game_id = game.storage.next_game_id
    
    new_deck = create_deck()
    players = [Player(id=i) for i in range(quantidadeJog)]
    
    new_game = game.Game(
        id_jogo=game_id,
        players=players,
        deck=new_deck,
        current_player_id=0  
    )
    
    for i in range(INITIAL_HAND_SIZE):
        for player in new_game.players:
            player.hand.append(game.draw_card_from_deck(new_game))
            
    new_game.discard_pile.append(game.draw_card_from_deck(new_game))
    
    game.storage.save_game(new_game)
    
    return {"id_jogo": game_id}

@app.get("/jogo/{id_jogo}/status")
def status_do_jogo(id_jogo: int):
    current_game = game.storage.get_game(id_jogo)
    return {
        "jogador_da_vez": current_game.current_player_id,
        "carta_no_topo": current_game.discard_pile[-1],
        "cartas_por_jogador": {f"jogador_{p.id}": len(p.hand) for p in current_game.players}
    }

@app.get("/jogo/{id_jogo}/jogador_da_vez")
def jogador_da_vez(id_jogo: int):
    current_game = game.storage.get_game(id_jogo)
    return {"jogador_da_vez": current_game.current_player_id}

@app.get("/jogo/{id_jogo}/{id_jogador}")
def ver_cartas(id_jogo: int, id_jogador: int):
    current_game = game.storage.get_game(id_jogo)
    
    if id_jogador < 0 or id_jogador >= len(current_game.players):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Jogador não encontrado")
        
    return {"hand": current_game.players[id_jogador].hand}


@app.put("/jogo/{id_jogo}/jogar")
def jogar_carta(id_jogo: int, id_jogador: int, id_carta: int = Query(..., ge=0)):
    current_game = game.storage.get_game(id_jogo)
    
    if id_jogador != current_game.current_player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Não é a vez do jogador {id_jogador}. É a vez do jogador {current_game.current_player_id}."
        )
        
    player = current_game.players[id_jogador]
    
    if id_carta < 0 or id_carta >= len(player.hand):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Índice de carta inválido.")
        
    card_to_play = player.hand[id_carta]
    top_card = current_game.discard_pile[-1]

    if card_to_play.color == top_card.color or card_to_play.value == top_card.value:
        played_card = player.hand.pop(id_carta)
        current_game.discard_pile.append(played_card)
        
        if not player.hand:
            current_game.game_over = True
            current_game.winner = id_jogador
            return {"message": f"Jogador {id_jogador} VENCEU O JOGO!"}
            
        current_game.current_player_id = (current_game.current_player_id + 1) % len(current_game.players)
        
        return {
            "message": f"Jogada válida. Próximo jogador: {current_game.current_player_id}",
            "proximo_jogador": current_game.current_player_id, 
            "carta_jogada": played_card
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Jogada inválida: A carta não combina em cor ou valor com a carta do topo."
        )

@app.put("/jogo/{id_jogo}/passa")
def passar_a_vez(id_jogo: int, id_jogador: int):
    current_game = game.storage.get_game(id_jogo)

    if id_jogador != current_game.current_player_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail=f"Não é a vez do jogador {id_jogador}. É a vez do jogador {current_game.current_player_id}."
        )

    new_card = game.draw_card_from_deck(current_game)
    current_game.players[id_jogador].hand.append(new_card)
    
    current_game.current_player_id = (current_game.current_player_id + 1) % len(current_game.players)
    
    return {
        "message": f"Você comprou uma carta. Próximo jogador: {current_game.current_player_id}",
        "proximo_jogador": current_game.current_player_id, 
        "nova_carta_comprada": new_card
    }