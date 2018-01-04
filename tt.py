import chess
import chess.polyglot
import copy
from log import l

# (C) 2017 by folkert@vanheusden.com
# released under AGPL v3.0

tt = []
tt_size = 0
tt_sub_size = 8
tt_age = 0

def tt_init(size):
	global tt_size, tt_sub_size, tt

	l('Set TT size to %d entries ' % size)
	tt_size = size

	dummy_move = chess.Move(0, 0)

	initial_entry = dict({ 'hash' : None, 'age' : -1, 'score' : None, 'flags': None, 'depth': -1, 'move': dummy_move })
	temp = [initial_entry.copy() for i in xrange(tt_sub_size)]

	tt = [copy.deepcopy(temp) for i in xrange(tt_size)]

def tt_inc_age():
	global tt_age

	tt_age += 1

def tt_calc_slot(h):
	global tt_size

	return h % tt_size

def tt_store(board, alpha, beta, score, move, depth):
	global tt_sub_size, tt, tt_age

	h = chess.polyglot.zobrist_hash(board)

	if score <= alpha:
		flags = 'U'
	elif score >= beta:
		flags = 'L'
	else:
		flags = 'E'

	record = { 'hash' : h,
		'score' : score,
		'flags' : flags,
		'depth' : depth,
		'age' : tt_age,
		'move' : move
		}

	idx = tt_calc_slot(h)

	use_ss = None

	use_ss2 = None
	min_depth = 99999

	for i in xrange(0, tt_sub_size):
		if tt[idx][i]['hash'] == h:
			if tt[idx][i]['depth'] > depth:
				return

			if flags != 'E' and tt[idx][i]['depth'] == depth:
				return

			tt[idx][i] = record

			return

		if tt[idx][i]['age'] != tt_age:
			use_ss = i
		elif tt[idx][i]['depth'] < min_depth:
			min_depth = tt[idx][i]['depth']
			use_ss2 = i

	if use_ss:
		tt[idx][use_ss] = record
	else:
		tt[idx][use_ss2] = record

def tt_lookup(board):
	global tt_sub_size, tt

	h = chess.polyglot.zobrist_hash(board)

	idx = tt_calc_slot(h)

	for i in xrange(0, tt_sub_size):
		if tt[idx][i]['hash'] == h:
			return tt[idx][i]

	return None

def tt_get_pv(b, first_move):
	pv = first_move.uci()

	board = b.copy()
	board.push(first_move)

	while True:
		hit = tt_lookup(board)
		if not hit:
			break

		pv += ' ' + hit['move'].uci()

		board.push(hit['move'])

	return pv
