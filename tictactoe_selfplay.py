import random
import time

def print_board(board):
    for row in board:
        print(" | ".join(row))
        print("-" * 9)

def check_winner(board, player):
    # Check rows, columns and diagonals
    for i in range(3):
        if all([cell == player for cell in board[i]]):
            return True
        if all([board[j][i] == player for j in range(3)]):
            return True
    if all([board[i][i] == player for i in range(3)]):
        return True
    if all([board[i][2 - i] == player for i in range(3)]):
        return True
    return False

def get_empty_cells(board):
    return [(i, j) for i in range(3) for j in range(3) if board[i][j] == ' ']

def play_game():
    board = [[' ' for _ in range(3)] for _ in range(3)]
    players = ['X', 'O']
    turn = 0
    print("Initial board:")
    print_board(board)
    while True:
        player = players[turn % 2]
        empty = get_empty_cells(board)
        if not empty:
            print("It's a draw!")
            break
        move = random.choice(empty)
        board[move[0]][move[1]] = player
        print(f"\nPlayer {player} moves to {move}")
        print_board(board)
        if check_winner(board, player):
            print(f"Player {player} wins!")
            break
        turn += 1
        time.sleep(1)

if __name__ == "__main__":
    play_game()
