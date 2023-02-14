from dataclasses import dataclass
import enum
import re
from collections import defaultdict
import sys
import time


class Piece():
    def __init__(self, color, pos):
        self.name = ""
        self.color = color # white is true
        self.coord = self.pos_to_coord(pos)

    def get_moves(self, board):
        return []

    def is_white(self):
        return self.color

    @staticmethod
    def pos_to_coord(pos):
        # Convert a position in "a1" ... "g8" format to row, col format
        col = ord(pos[0]) - ord('a')
        row = int(pos[1]) - 1
        return row, col

    @staticmethod
    def coord_to_pos(coord):
        # Convert a position in row, col format to "a1" ... "g8" format
        row, col = coord
        pos = chr(col + ord('a')) + str(row + 1)
        return pos
    
    @staticmethod
    def coord_within_range(coord):
        return 0 <= coord[0] < 8 and 0 <= coord[1] < 8

    def __str__(self):
        return self.name.upper() if self.is_white() else self.name.lower()

class Rook(Piece):
    def __init__(self, color, pos):
        super().__init__(color, pos)
        self.name = 'R'
        self.captured = False

    def get_moves(self, board):
        if self.captured:
            return []

        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        moves = []
        for dx, dy in directions:
            new_coord = (self.coord[0] + dx, self.coord[1] + dy)
            while Piece.coord_within_range(new_coord) and new_coord != board.wk.coord:
                moves.append(new_coord)
                new_coord = (new_coord[0] + dx, new_coord[1] + dy)
        return list(map(Piece.coord_to_pos, moves))

class King(Piece):
    def __init__(self, color, pos):
        super().__init__(color, pos)
        self.name = "K"

    def get_moves(self, board):
        directions = [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]
        moves = []
        for dx, dy in directions:
            new_coord = (self.coord[0] + dx, self.coord[1] + dy)
            if not Piece.coord_within_range(new_coord):
                continue
            if new_coord == board.wr.coord and self.color:
                continue
                
            moves.append(new_coord)
        return list(map(Piece.coord_to_pos, moves))

    def attacked_squares(self, board): 
        # this is needed to deal with the case where black king can capture the rook
        # but the area the rook is in is guarded by the white king, so we need to know what 
        # cells are guarded by the white king
        directions = [(-1, 1), (0, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (0, -1), (1, -1)]
        moves = []
        for dx, dy in directions:
            new_coord = (self.coord[0] + dx, self.coord[1] + dy)
            if not Piece.coord_within_range(new_coord):
                continue
            moves.append(new_coord)
        return list(map(Piece.coord_to_pos, moves)) 

# only treating a special case with the two kings and a white rook
class Board:
    def __init__(self, wk, wr, bk, white_turn=True):
        self.wk = King(True, wk)
        self.bk = King(False, bk)
        self.wr = Rook(True, wr)
        self.white_turn = white_turn
        self.move_stack = []
        self.state_stack = []
        self._legal_moves = {}

    @classmethod
    def from_fen(cls, fen):
        fen_parts = fen.split()
        white_turn = fen_parts[1]=='w'
        fen = re.sub(r'(\d+)', lambda match: '.' * int(match.group(0)), fen_parts[0])
        board = fen.replace('/', '')
        wk_index = board.index('K')
        bk_index = board.index('k')
        wr_index = board.index('R')
        wk_pos = Piece.coord_to_pos((7-(wk_index // 8), wk_index % 8))
        bk_pos = Piece.coord_to_pos((7-(bk_index // 8), bk_index % 8))
        wr_pos = Piece.coord_to_pos((7-(wr_index // 8), wr_index % 8))
        return cls(wk_pos, wr_pos, bk_pos, white_turn=white_turn)

    def is_check(self):
        bk = self.bk.coord
        wr = self.wr.coord
        wk = self.wk.coord
        if self.white_turn: # black can't put white in check
            return False
        else: 
            # Check if the black king is in the same row as the rook
            if bk[0] == wr[0]:
                # Check if the white king is not blocking the rook's attack
                if wk[0] == bk[0]:
                    return not(min(bk[1], wr[1]) < wk[1] < max(bk[1], wr[1]))
                else:
                    return True
            # Check if the black king is in the same column as the rook
            elif bk[1] == wr[1]:
                # Check if the white king is not blocking the rook's attack
                if wk[1] == bk[1]:
                    return not(min(bk[0], wr[0]) < wk[0] < max(bk[0], wr[0]))
                else:
                    return True
            # Black king is not in check
            return False

    def copy(self):
        wk = Piece.coord_to_pos(self.wk.coord)
        bk = Piece.coord_to_pos(self.bk.coord)
        wr = Piece.coord_to_pos(self.wr.coord)
        return Board(wk, wr, bk, white_turn=self.white_turn)

    def unique_id(self):
        bk_hash = self.bk.coord[0] * 8 + self.bk.coord[1]
        wk_hash = self.wk.coord[0] * 8 + self.wk.coord[1]
        wr_hash = self.wr.coord[0] * 8 + self.wr.coord[1]
        # first bit for white_turn, next 7 bits for bk_hash, ... etc
        return (1 if self.white_turn else 0) + 2 * (bk_hash + 64 * (wk_hash + wr_hash * 64))

    def evaluate(self):
        # Check if the black king is in check
        if self.is_check():
            # Check if the black king is in checkmate
            if self.is_checkmate():
                # Return a score indicating a win for white
                return 1000
            # Return a score indicating that the black king is in check
            return 50
        # Check if the game is in a stalemate
        elif self.is_stalemate():
            # Return a score indicating a draw
            return 0
        # Return a score indicating an ongoing game
        return 1

    def push_move(self, move, debug=False):
        # Check if the move is legal
        if move not in self.legal_moves:
            return False
        self.move_stack.append(move)
        state = (self.wk.coord, self.wr.coord, self.bk.coord, self.wr.captured)
        self.state_stack.append(state)

        self.make_move(move)
        return True

    def pop(self):
        if len(self.move_stack) == 0:
            return None
        popped_move = self.move_stack.pop()
        state = self.state_stack.pop()
        wk_coord, wr_coord, bk_coord, wr_captured = state
        self.wk.coord = wk_coord
        self.bk.coord = bk_coord
        self.wr.coord = wr_coord
        self.wr.captured = wr_captured

        self.white_turn = not self.white_turn

        return popped_move

    # returns a new board with move made
    def make_move(self, move):
        start_coord, end_coord = Piece.pos_to_coord(move[:2]), Piece.pos_to_coord(move[2:])

        # if the move results in rook capture mark it as so
        if end_coord == self.wr.coord:
            self.wr.captured = True

        # Update the positions of the pieces to reflect the move
        if start_coord == self.wk.coord:
            self.wk.coord = end_coord
        elif start_coord == self.bk.coord:
            self.bk.coord = end_coord
        elif start_coord == self.wr.coord:
            self.wr.coord = end_coord

        self.white_turn = not self.white_turn

    def is_checkmate(self):
        if self.white_turn: # white can't be checkmated
            return False
        else: 
            # if the black king is in check and doesn't have move it's a stalemate
            return self.is_check() and len(self.legal_moves) == 0

    def is_stalemate(self):
        return self.wr.captured or (not self.is_check() and len(self.legal_moves) == 0)

    @property
    def legal_moves(self):
        if self.unique_id() in self._legal_moves:
            return self._legal_moves[self.unique_id()]

        ret = None
        if self.white_turn:
            # there can't be any discovery attacks so it's pretty straighforward
            attacked_squares = set(self.bk.get_moves(self))
            king_pseudo_legal_moves = [Piece.coord_to_pos(self.wk.coord) + dst_pos for dst_pos in self.wk.get_moves(self)]
            rook_pseudo_legal_moves = [Piece.coord_to_pos(self.wr.coord) + dst_pos for dst_pos in self.wr.get_moves(self)]
            ret = rook_pseudo_legal_moves + [move for move in king_pseudo_legal_moves if move[2:] not in attacked_squares]
        else:
            white_king_attacked_squares = set(self.wk.attacked_squares(self))
            white_rook_attacked_squares = set(self.wr.get_moves(self))
            pseudo_legal_moves = [Piece.coord_to_pos(self.bk.coord) + dst_pos for dst_pos in self.bk.get_moves(self)]
            moves = []
            for move in pseudo_legal_moves:
                dst = move[2:]
                if dst in white_king_attacked_squares:
                    continue
                if dst in white_rook_attacked_squares and dst != Piece.coord_to_pos(self.wr.coord): # to deal with king capturing rook
                    continue
                moves.append(move)
            ret = moves

        self._legal_moves[self.unique_id()] = ret
        return ret

    def __repr__(self):
        names = defaultdict(lambda: '.')
        d = [(self.bk.coord, str(self.bk)), (self.wk.coord, str(self.wk))]
        d = d + [(self.wr.coord, str(self.wr))] if not self.wr.captured else d
        names.update(d)
        return "\n".join([" ".join([names[(y,x)] for x in range(8)]) for y in reversed(range(8))])

class TTEntryFlag(enum.Enum):
    EXACT = 0
    LOWERBOUND = 1
    UPPERBOUND = 2

@dataclass
class TTEntry:
    value: tuple
    depth: int
    flag: TTEntryFlag

transposition_table = {}

def transpositionTableLookup(board_id):
    ttEntry = transposition_table.get(board_id, None)
    return ttEntry

def transpositionTableStore(board_id, depth, value, flag):
    transposition_table[board_id] = TTEntry(value=value, depth=depth, flag=flag)

def negamax(board, depth, alpha=float('-inf'), beta=float('inf'), color=1):
    board_id = board.unique_id()
    # check transposition table
    alphaOrig = alpha
    ttEntry = transpositionTableLookup(board_id)#transposition_table.get(board_id, None)
    if ttEntry is not None and ttEntry.depth >= depth:
        if ttEntry.flag == TTEntryFlag.EXACT:
            return ttEntry.value
        elif ttEntry.flag == TTEntryFlag.LOWERBOUND:
            alpha = max(alpha, ttEntry.value[0])    
        elif ttEntry.flag == TTEntryFlag.UPPERBOUND:
            beta = min(beta, ttEntry.value[0])

        if alpha >= beta:
            return ttEntry.value

    if depth == 0 or board.is_checkmate() or board.is_stalemate():
        evaluation = board.evaluate()
        return color * (depth + 1) * evaluation, None

    best_move = None
    for move in board.legal_moves:
        board.push_move(move)
        evaluation, _ = negamax(board, depth - 1, -beta, -alpha, -color)
        evaluation = -evaluation
        board.pop()

        if evaluation > alpha:
            alpha = evaluation
            best_move = move

        if alpha >= beta:
            break
    
    # update transposition table
    value = (alpha, best_move)

    if value[0] <= alphaOrig:
        ttEntry_flag = TTEntryFlag.UPPERBOUND
    elif value[0] >= beta:
        ttEntry_flag = TTEntryFlag.LOWERBOUND
    else:
        ttEntry_flag = TTEntryFlag.EXACT

    #transposition_table[board_id] = TTEntry(value=value, depth=depth, flag=ttEntry_flag)
    transpositionTableStore(board_id, depth, value, ttEntry_flag)
    return value


def main():
    #rand_fen, base_board = generate_valid_board()
    #test_fen = "8/8/8/7R/8/4K3/8/4k3 w - - 4 3" # mate in 1
    #test_fen = "6k1/8/5K2/8/8/8/3R4/8 w - - 4 3" # mate in 3
    #test_fen = "8/8/8/8/8/4R3/4K3/7k w - - 4 3" # mate in 5?
    #test_fen = "8/4K3/6k1/5R2/8/8/8/8 w - - 0 1" # mate in 11?
    test_fen = "8/8/8/k7/8/KR6/8/8 w - - 0 1" # mate in 9?
    #base_board = chess.Board(test_fen)

    #wk, wr, bk = input().split()
    #my_board = Board(wk, wr, bk)
    my_board = Board.from_fen(test_fen)
    #best_moves_dict = {}
    start = time.process_time()
    depth = 11
    best_eval, best_move = negamax(my_board, depth)
    #print(len(best_moves_dict))
    print(time.process_time() - start, "seconds", file=sys.stderr)
    print(best_eval, best_move, file=sys.stderr)
    print(my_board.move_stack)
    mate_len = 0
    i = 0
    while not my_board.is_stalemate() and not my_board.is_checkmate() and i < 25:
        #base_board.push_uci(best_move)
        transposition_table = {}
        if i != 0:
            best_eval, best_move = negamax(my_board, depth )
        transposition_table = {}
    #    best_eval, best_move = transposition_table[my_board.unique_id()].value
        print(my_board, file=sys.stderr)
        print(best_eval, best_move, file=sys.stderr)
        mate_len += 1
        my_board.push_move(best_move, debug=True)
        if my_board.is_stalemate() or my_board.is_checkmate():
            break

        best_eval, best_move = negamax(my_board, depth)
        transposition_table = {}
        #    best_eval, best_move = transposition_table[my_board.unique_id()].value
        print(my_board, file=sys.stderr)
        print(best_eval, best_move, file=sys.stderr)

        mate_len += 1
        my_board.push_move(best_move)
        i += 1

    print(my_board, file=sys.stderr)
    print(best_eval, best_move, file=sys.stderr)
    print(mate_len)

if __name__ == "__main__":
    main()
    