import chess
import chess.polyglot
from log import l

# (C) 2017 by folkert@vanheusden.com
# released under AGPL v3.0

tt = []
tt_size = 0
tt_sub_size = 8
tt_age = 0

tt_stats_store_count = tt_stats_store_hit = tt_stats_store_hit_store = tt_stats_miss_store = tt_stats_store_depth = None
tt_stats_lookup_cnt = tt_stats_lookup_hit = tt_stats_lookup_miss = None

def tt_reset_stats():
	global tt_stats_store_count, tt_stats_store_hit, tt_stats_store_hit_store, tt_stats_miss_store, tt_stats_lookup_cnt, tt_stats_lookup_hit, tt_stats_lookup_miss, tt_stats_store_depth

	tt_stats_store_count = tt_stats_store_hit = tt_stats_store_hit_store = tt_stats_miss_store = tt_stats_store_depth = 0
	tt_stats_lookup_cnt = tt_stats_lookup_hit = tt_stats_lookup_miss = 0

def tt_get_stats():
	global tt_stats_store_count, tt_stats_store_hit, tt_stats_store_hit_store, tt_stats_miss_store

	return {
		"tt_stats_store_count" : tt_stats_store_count,
		"tt_stats_store_hit" : tt_stats_store_hit,
		"tt_stats_store_hit_store" : tt_stats_store_hit_store,
		"tt_stats_store_depth" : tt_stats_store_depth,
		"tt_stats_miss_store" : tt_stats_miss_store,
		"tt_stats_lookup_cnt" : tt_stats_lookup_cnt,
		"tt_stats_lookup_hit" : tt_stats_lookup_hit,
		"tt_stats_lookup_miss" : tt_stats_lookup_miss
		}

def tt_init(size):
	global tt_size, tt_sub_size, tt

	l('Set TT size to %d entries ' % size)
	tt_size = size

	dummy_move = chess.Move(0, 0)

	initial_entry = dict({ 'hash' : None, 'age' : -1, 'score' : None, 'flags': None, 'depth': -1, 'move': dummy_move })
	temp = [initial_entry.copy() for i in xrange(tt_sub_size)]

	tt = [temp for i in xrange(tt_size)]

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

	global tt_stats_store_count
	tt_stats_store_count += 1

	for i in xrange(0, tt_sub_size):
		if tt[idx][i]['hash'] == h:
			global tt_stats_store_hit
			tt_stats_store_hit += 1

			if tt[idx][i]['depth'] > depth:
				tt_stats_store_depth += 1
				return

			if flags != 'E' and tt[idx][i]['depth'] == depth:
				tt_stats_store_depth += 1
				return

			tt[idx][i] = record

			global tt_stats_store_hit_store
			tt_stats_store_hit_store += 1

			return

		if tt[idx][i]['age'] != tt_age:
			use_ss = i
		elif tt[idx][i]['depth'] < min_depth:
			min_depth = tt[idx][i]['depth']
			use_ss2 = i

	global tt_stats_miss_store
	tt_stats_miss_store += 1

	if use_ss:
		tt[idx][use_ss] = record
	else:
		tt[idx][use_ss2] = record

def tt_lookup(board):
	global tt_sub_size, tt

	h = chess.polyglot.zobrist_hash(board)

	idx = tt_calc_slot(h)

	global tt_stats_lookup_cnt
	tt_stats_lookup_cnt += 1

	for i in xrange(0, tt_sub_size):
		if tt[idx][i]['hash'] == h:
			global tt_stats_lookup_hit
			tt_stats_lookup_hit += 1

			return tt[idx][i]

	global tt_stats_lookup_miss
	tt_stats_lookup_miss += 1

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
