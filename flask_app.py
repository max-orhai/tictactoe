
from json import dumps
from random import choice

from flask import Flask, request
from werkzeug import Headers

from tictactoe import make_tables


plain = Headers([('Content-Type', 'text/plain')])
json  = Headers([('Content-Type', 'application/json')])

# Just be patient, this only has to happen once!
tuff_table, nice_table = make_tables()

# Might as well cache the JSON while we're at it.
tuff_table_json = dumps(tuff_table, indent=0, sort_keys=True)
nice_table_json = dumps(nice_table, indent=0, sort_keys=True)


def lookup(board, space=' ', table=nice_table):
    if not board or (space not in board and '+' not in board):
        return ("""
                TIC TAC TOE (I'm player 'o')
Hi! I play tic tac toe (naughts and crosses), by responding to
a 'board' parameter in the URL query string with another board
that shows my countermove. Use ?board=+++++++++ to give me the
first move, or you can move first by placing an 'x' in a board
like this: ?board=+x++++++++. I also accept URL-encoded '%20'
space characters instead of '+' to denote empty squares on the
board, or you can use your own space-encoding character if you
pass a '_' query param; for example ?_=-&board=--x------. I'll
use your space char in my output, if you give one; otherwise I
will use a literal ' ' space. I only accept '_', '-', '.', and
'+' or ' ' as escaped spaces. The board indices run left-right
and top-bottom on the 3x3 grid like this:

     0 1 2           o x o                    012345678
     3 4 5  so that  x o    encodes as ?board=oxoxo++x+ 
     6 7 8             x

There's a """ + ('more' if table is nice_table else 'less')
              + ' aggressive version of me at /tictactoe'
              + ('' if table is nice_table else '/nice') + """

You can get my table of moves at /tictactoe"""
              + ('/nice' if table is nice_table else '')
              + """/table.json
You can get my Python 2.7 source code at /tictactoe/code.tar
              (c) Max Orhai, January 2016.\n""", 400, plain)

    # normalize space and plus chars to dots as used in table
    board = board.replace(space, '.').replace('+', '.')
    if len(board) != 9 or set(board) - set('xo.'):
        return ("Invalid board format. Try ?board=++o+x++++"
                + " or ?_=.&board=..x.o....", 400, plain)
    moves = table.get(board)
    if moves is None:
        return ("Unreachable board state: I'm player O. " +
                ("Must have been a typo?" if table is nice_table
                 else "Are you trying to cheat?"), 400, plain)

    # choose a random move
    return choice(moves).replace('.', space), 200, plain


assert lookup('xo trash ')[1] == 400  # bad chars
assert lookup('        ' )[1] == 400  # bad length
assert lookup('xoxoxoxox')[1] == 400  # board is full
assert lookup('xxx   ooo')[1] == 400  # unreachable
assert lookup('    o    ')[1] == 400  # unreachable
assert lookup('    x    ')[1] == 200
assert lookup('++++x++++')[1] == 200  
assert lookup('@@@@x@@@@', '@')[1] == 200
assert lookup('....x....', '.')[1] == 200
assert len({lookup('++++x++++')[0] for _ in range(20)}) > 1


app = Flask(__name__)

def lookup_from_request(table):
    space = request.args.get('_')
    if space not in ('+ ', '-', '_', '.'):
        space = ' '
    return lookup(board=request.args.get('board'),
                  space=space, table=table)

@app.route('/tictactoe')
def tuff(): return lookup_from_request(tuff_table)

@app.route('/tictactoe/nice')
def nice(): return lookup_from_request(nice_table)

@app.route('/tictactoe/table.json')
def tuff_json(): return tuff_table_json, 200, json

@app.route('/tictactoe/nice/table.json')
def nice_json(): return nice_table_json, 200, json
