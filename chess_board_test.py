import chess
import unittest
from rook_mate import Board
import random
import re

def generate_fen(white_to_play=True):
    dots = ['.' for i in range(64-3)]
    pieces = ['K', 'k', 'R']
    all_pieces = dots + pieces
    random.shuffle(all_pieces)
    board = [all_pieces[i:i+8] for i in range(0, len(all_pieces), 8)]
    fen_rows = []
    for row in board:
        fen_row = ''.join(row)
        fen_row = re.sub(r'(\.+)', lambda match: str(len(match.group(0))), fen_row)
        fen_rows.append(fen_row)
    fen = '/'.join(fen_rows)
    return f'{fen} {"w" if white_to_play else "b"} - - 0 1'

def generate_valid_board(white_to_play=True):
    base_board = None
    rand_fen = ""
    i = 0
    while i < 1000:
        rand_fen = generate_fen(white_to_play)
        base_board = chess.Board(rand_fen)
        i += 1
        if base_board.status() == chess.STATUS_VALID:
            break
    return rand_fen, base_board

class TestChessBoard(unittest.TestCase):
    def test_is_check(self):
        for _ in range(100):
            rand_fen, base_board = generate_valid_board(white_to_play=False)
            my_board = Board.from_fen(rand_fen)
            self.assertEqual(my_board.is_check(), base_board.is_check())

    def test_legal_moves(self):
        num_tests = 100
        for i in range(num_tests):
            rand_fen, base_board = generate_valid_board(white_to_play=False if i < num_tests//2 else True)
            my_board = Board.from_fen(rand_fen)
            my_legal_moves = sorted(my_board.legal_moves)
            base_legal_moves = sorted(map(str,base_board.legal_moves))
            check = base_legal_moves == my_legal_moves
            if not check:
                print(base_legal_moves)
                print(my_legal_moves)
                print(base_board)
            self.assertEqual(base_legal_moves, my_legal_moves)

    def test_is_checkmate(self):
        for _ in range(100):
            rand_fen, base_board = generate_valid_board(white_to_play=False)
            my_board = Board.from_fen(rand_fen)
            if base_board.is_checkmate() != my_board.is_checkmate():
                print(my_board.bk.get_moves(my_board))
                print(base_board)
            self.assertEqual(my_board.is_checkmate(), base_board.is_checkmate())

    def test_make_move(self):
        total_moves = 0
        max_moves = 100
        for _ in range(max_moves):
            rand_fen, base_board = generate_valid_board(white_to_play=False)
            my_board = Board.from_fen(rand_fen)
            for _ in range(20):
                if total_moves >= max_moves: return
                if base_board.is_game_over(): break
                if len(my_board.move_stack) == 0 or random.choice([True, False]):
                    base_legal_moves = sorted(map(str,base_board.legal_moves))
                    random_move = random.choice(base_legal_moves)
                    base_board.push_uci(random_move)
                    my_board.push_move(random_move)
                    my_legal_moves = sorted(my_board.legal_moves)
                    base_legal_moves = sorted(map(str,base_board.legal_moves))
                    check = base_legal_moves == my_legal_moves
                    if not check:
                        print(base_legal_moves)
                        print(my_legal_moves)
                        print(base_board)
                    self.assertEqual(base_legal_moves, my_legal_moves)
                else:
                    base_board.pop()
                    popped = my_board.pop()
                    my_legal_moves = sorted(my_board.legal_moves)
                    base_legal_moves = sorted(map(str,base_board.legal_moves))

                    check = base_legal_moves == my_legal_moves
                    if not check:
                        print(popped)
                        print(base_legal_moves)
                        print(my_legal_moves)
                        print(base_board)
                    self.assertEqual(base_legal_moves, my_legal_moves)

                total_moves += 1

def main():
    random.seed(1)
    # Create a test suite by passing the test class to unittest.TestSuite
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestChessBoard))

    # Create a runner and run the tests
    runner = unittest.TextTestRunner() 
    result = runner.run(suite)

if __name__ == "__main__":
    main()