
# A tic-tac-toe player by Max Orhai, 2016 January 28 -- 30.
#
# Goal: Play to win, and put up a good fight in any case.
# Secondary goal: reach every nonlosing path in the game tree.
# Strategy:
#    Build the entire game tree,
#      mark its losing and winning paths, then prune losing paths from tree,
#      preferring known-winning next states when available, and retaining the
#      entire set of winning or nonlosing countermoves for any reachable move.
#    Flatten tree into a single table for easy use by flask app or other UI.

testing = False
#testing = True  #  run test suite at load time

# board format: 9-char string of 'x', 'o', or '.' with index <===> grid
lines = [(0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows            0 1 2
         (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns         3 4 5
         (0, 4, 8), (2, 4, 6)]             # diagonals       6 7 8 


def score_for(board):
    for a, b, c in lines:
        abc = board[a] + board[b] + board[c]
        if abc == 'ooo': return  1  # win
        if abc == 'xxx': return -1  # lose
    if '.' in board:
        return None  # further moves are possible
    return 0  # board is full, it's a tie


def all_next_boards(board, player):
    boards = []
    for index, value in enumerate(board):
        if value == '.':
            boards.append(board[0:index] + player + board[(index + 1):])
    return boards


class GameState(object):
    winning = losing = score = None

    def __init__(self, board, player):
        if testing:  # catch invalid input
            assert len(board) == 9
            assert not(set(board) - set('xo.'))
            assert player in 'xo'
        
        self.board, self.player = board, player
        self.next_player = 'x' if self.player == 'o' else 'o'
        self.score = score_for(self.board)
        if self.score is None:
            # recursively build out the subtrees
            self.moves = [GameState(board, self.next_player) for board
                          in all_next_boards(self.board, self.player)]

    def __repr__(self):
        return ('<' + self.board + '|' + self.player
                    + ('W' if self.winning else '')
                    + ('L' if self.losing  else '')
                    + (str(self.score) if self.score is not None else '')
                    + '>')

    def mark(self):
        if self.score is None:
            # walk tree bottom-up, from leaves to root
            for gst in self.moves:
                gst.mark()
            if self.player == 'o':
                self.winning = any(gst.winning for gst in self.moves)
                self.losing  = all(gst.losing  for gst in self.moves)
            else:
                self.winning = all(gst.winning for gst in self.moves)
                self.losing  = any(gst.losing  for gst in self.moves)
        else:
            self.losing  = self.score == -1  # these are both always 
            self.winning = self.score ==  1  # relative to player o

    def prune(self):
        if self.score is None:
            if self.player == 'o':  # we have no control over player x
                self.moves = filter(
                    lambda gst: gst.winning if self.winning else
                                not gst.losing, self.moves)
            # walk tree top-down, from root to leaves
            for gst in self.moves:
                gst.prune()

    def flattened(self):
        # walk the game tree and collect all states into
        # a single {their_board: [my_boards]} dict
        table = {}
        if self.score is None:
            if self.player == 'o':  # only save player o's moves
                table[self.board] = [gst.board for gst in self.moves]
            for gst in self.moves:
                table.update(gst.flattened())
        else:
            return {}
        return table


def make_tables():
    # return a pair (tuff, nice) of tables:
    #   tuff: o always plays the center on an empty board
    #   nice: o's first move is unconstrained
    x_tree = GameState('.........', player='x')
    x_tree.mark()
    x_tree.prune()
    x_dict = x_tree.flattened()
    
    o_tree = GameState('.........', player='o')
    o_tree.mark()
    o_tree.prune()
    o_dict_nice = o_tree.flattened()
    
    if testing:
        # the two sets of inputs should not intersect
        assert not (x_dict.viewkeys() & o_dict_nice.viewkeys())

    o_tree.moves = [gst for gst in o_tree.moves
                    if gst.board == '....o....']
    o_dict_tuff = o_tree.flattened()

    nice_table = x_dict.copy()
    tuff_table = x_dict.copy()
    nice_table.update(o_dict_nice)
    tuff_table.update(o_dict_tuff)
    return tuff_table, nice_table
   

def test_table(move_table):
    def count(score):
        assert score != -1  # never lose
        global tie_counter, win_counter
        if score == 0: tie_counter += 1
        if score == 1: win_counter += 1

    assert move_table  # should be nonempty 
    for board, moves in move_table.iteritems():
        assert score_for(board) is None # o can move
        assert moves  # should always be nonempty
        for move in moves:
            score = score_for(move)
            count(score)
            if score not in (0, 1): # stop after a tie or win
                for next_x_move in all_next_boards(move, 'x'):
                    next_x_move_score = score_for(next_x_move)
                    if next_x_move_score is None:
                        assert next_x_move in move_table
                    count(next_x_move_score)
    print(str(len(move_table)) + ' countered x moves, '
            + str(win_counter) + ' wins, '
            + str(tie_counter) + ' ties')


if testing:
    tuff, nice = make_tables()
    tie_counter = win_counter = 0
    print('tuff: (o, given first move, always plays the center)')
    test_table(tuff)
    tie_counter = win_counter = 0
    print('nice: (o, given first move, can play any square)')
    test_table(nice)
 