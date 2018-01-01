#! /usr/bin/python

# (C) 2017 by folkert@vanheusden.com
# released under AGPL v3.0

import chess
import chess.pgn
from psq import psq, psq_individual
from tt import tt_inc_age, tt_store, tt_lookup, tt_get_pv
from log import l
from operator import itemgetter
import math
import sys
import threading
import time

stats_node_count = 0
stats_tt_checks = stats_tt_hits = 0

infinite = 101000
checkmate = 10000

material_table = {
	'P' : 100, 'p' : 100,
	'N' : 325, 'n' : 325,
	'B' : 325, 'b' : 325,
	'R' : 500, 'r' : 500,
	'Q' : 975, 'q' : 975,
	'K' : 10000, 'k' : 10000
	}

pmaterial_table = {
	chess.PAWN : 100,
	chess.KNIGHT : 325,
	chess.BISHOP : 325,
	chess.ROOK : 500,
	chess.QUEEN : 975,
	chess.KING : 10000
	}

to_flag = None

def set_to_flag(to_flag):
	to_flag.set()

def get_stats():
	global stats_node_count, stats_tt_hits, stats_tt_checks

	return { 'stats_node_count' : stats_node_count,
		'stats_tt_hits' : stats_tt_hits,
		'stats_tt_checks' : stats_tt_checks }

def reset_stats():
	global stats_node_count, stats_tt_hits, stats_tt_checks

	stats_node_count = stats_tt_checks = stats_tt_hits = 0

def material(board):
	score = 0

	for pos in chess.SQUARES:
		piece = board.piece_at(pos)
		if not piece:
			continue

		if piece.color: # white
			score += material_table[piece.symbol()]
		else:
			score -= material_table[piece.symbol()]

	return score

def mobility(board):
        if board.turn:
                white_n = board.legal_moves.count()

                board.push(chess.Move.null())
                black_n = board.legal_moves.count()
                board.pop()

        else:
                black_n = board.legal_moves.count()

                board.push(chess.Move.null())
                white_n = board.legal_moves.count()
                board.pop()

        return white_n - black_n

def evaluate(board):
	score = material(board)

	score += psq(board) / 4

	score += mobility(board) * 10

	if board.turn:
		return score

	return -score

def pc_to_list(board, moves_first):
	out = []

	for m in board.legal_moves:
		score = 0

		if m.promotion:
			score += pmaterial_table[m.promotion] << 8

		victim = board.piece_at(m.to_square)
		if victim:
			score += material_table[victim.symbol()] << 8

		else:
			me = board.piece_at(m.from_square)

			score += psq_individual(m.to_square, me) - psq_individual(m.from_square, me)

		record = { 'score' : score, 'move' : m }

		out.append(record)

	for i in xrange(0, len(moves_first)):
		for m in out:
			if m['move'] == moves_first[i]:
				m['score'] = infinite - i

	return sorted(out, key=itemgetter('score'), reverse = True) 

def blind(board, m):
	victim = board.piece_at(m.to_square)
	victim_eval = material_table[victim.symbol()]

	me = board.piece_at(m.from_square)
	me_eval = material_table[me.symbol()]

	return victim_eval < me_eval and board.attackers(not board.turn, m.to_square)

def is_draw(board):
	return board.is_stalemate() or board.is_insufficient_material() or board.can_claim_threefold_repetition() or board.can_claim_fifty_moves() or board.can_claim_draw()

def qs(board, alpha, beta):
	global to_flag
	if to_flag.is_set():
		return -infinite

	global stats_node_count
	stats_node_count += 1

	if board.is_checkmate():
		return -checkmate

	if is_draw(board):
		return 0

	best = -infinite

	is_check = board.is_check()
	if not is_check:
		best = evaluate(board)

		if best > alpha:
			alpha = best

			if best >= beta:
				return best

	moves = pc_to_list(board, [])

	move_count = 0
	for m_work in moves:
		m = m_work['move']

		is_capture_move = board.piece_at(m.to_square) != None

		if is_check == False and is_capture_move == False and m.promotion == None:
			continue

		if is_capture_move and blind(board, m):
			continue

		move_count += 1

		board.push(m)

		score = -qs(board, -beta, -alpha)

		board.pop()

		if score > best:
			best = score

			if score > alpha:
				alpha = score

				if score >= beta:
					break

	return best

def tt_lookup_helper(board, alpha, beta, depth):
	tt_hit = tt_lookup(board)
	if not tt_hit:
		return None

	if tt_hit['move'] != None and not tt_hit['move'] in board.legal_moves:
		return None

	rc = (tt_hit['score'], tt_hit['move'])

	if tt_hit['depth'] < depth:
		return [ False, rc ]

	if tt_hit['flags'] == 'E':
		return [ True, rc ]

	if tt_hit['flags'] == 'L' and tt_hit['score'] >= beta:
		return [ True, rc ]

	if tt_hit['flags'] == 'U' and tt_hit['score'] <= alpha:
		return [ True, rc ]

	return [ False, rc ]

def search(board, alpha, beta, depth, siblings, max_depth):
	global to_flag
	if to_flag.is_set():
		return (-infinite, None)

	if depth == 0:
		return (qs(board, alpha, beta), None)

	top_of_tree = depth == max_depth

	global stats_node_count
	stats_node_count += 1

	global stats_tt_checks
	stats_tt_checks += 1
	tt_hit = tt_lookup_helper(board, alpha, beta, depth)
	if tt_hit:
		global stats_tt_hits
		stats_tt_hits += 1

		if tt_hit[0]:
			return tt_hit[1]

	alpha_orig = alpha

	if board.is_checkmate():
		return (-checkmate, None)

	if is_draw(board):
		return (0, None)

	best = -infinite
	best_move = None

	### NULL MOVE ###
	if not board.is_check() and depth >= 3 and not top_of_tree:
		board.push(chess.Move.null())
		result = search(board, -beta, -beta + 1, depth - 3, [], depth - 3)
		board.pop()

		if result[0] >= beta:
			return [result[0], None]
	#################

	moves_first = []
	if tt_hit and tt_hit[1][1]:
		moves_first.append(tt_hit[1][1])

	moves_first += siblings

	moves = pc_to_list(board, moves_first)

	new_siblings = []

	move_count = 0
	for m_work in moves:
		m = m_work['move']
		move_count += 1

		new_depth = depth - 1

		if depth >= 3 and move_count >= 4:
			new_depth -= 1

			if move_count >= 6:
				new_depth -= 1

		board.push(m)

		result = search(board, -beta, -alpha, new_depth, new_siblings, max_depth)
		score = -result[0]

		board.pop()

		if score > best:
			best = score
			best_move = m

			if score > alpha:
				alpha = score

				if len(siblings) == 2:
					del siblings[-1]
				siblings.insert(0, m)

				if score >= beta:
					break

	if move_count > 0:
		tt_store(board, alpha_orig, beta, best, best_move, depth)

	return (best, best_move)

def calc_move(board, max_think_time, max_depth):
	global to_flag
	to_flag = threading.Event()
	to_flag.clear()

	t = None
	if max_think_time:
		t = threading.Timer(max_think_time, set_to_flag, args=[to_flag])
		t.start()

	reset_stats()

	l(board.fen())

	tt_inc_age()

	result = None

	alpha = -infinite
	beta = infinite

	siblings = []
	start_ts = time.time()
	for d in xrange(1, max_depth + 1):
		cur_result = search(board, alpha, beta, d, siblings, d)

		diff_ts = time.time() - start_ts

		if to_flag.is_set():
			if result:
				result[3] = diff_ts
			break

		stats = get_stats()

		if cur_result[1]:
			diff_ts_ms = math.ceil(diff_ts * 1000.0)

			pv = tt_get_pv(board, cur_result[1])
			msg = 'depth %d score cp %d time %d nodes %d pv %s' % (d, cur_result[0], diff_ts_ms, stats['stats_node_count'], pv)

			print 'info %s' % msg
			sys.stdout.flush()

			l(msg)

		result = [cur_result[0], cur_result[1], d, diff_ts]

		if max_think_time and diff_ts > max_think_time / 2.0:
			break

		if cur_result[0] <= alpha:
			alpha = -infinite
		elif cur_result[0] >= beta:
			beta = infinite
		else:
			alpha = cur_result[0] - 50
			if alpha < -infinite:
				alpha = -infinite

			beta = cur_result[0] + 50
			if beta > infinite:
				beta = infinite

		#l('a: %d, b: %d' % (alpha, beta))

	if t:
		t.cancel()

	l(board.legal_moves)

	if result == None or result[1] == None:
		l('random move!')
		m = None

		for m in board.legal_moves:
			break

		result = [ 0, m, 0, time.time() - start_ts ]

	l(result)

	diff_ts = time.time() - start_ts
	stats = get_stats()
	l('nps: %f, nodes: %d, tt_hits: %f%%' % (stats['stats_node_count'] / diff_ts, stats['stats_node_count'], stats['stats_tt_hits'] * 100.0 / stats['stats_tt_checks']))

	return result
