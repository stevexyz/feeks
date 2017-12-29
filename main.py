#! /usr/bin/python

# (C) 2017 by folkert@vanheusden.com
# released under AGPL v3.0

import chess
import chess.pgn
import sys
import traceback
from tt import tt_init
from brain import calc_move, cm_thread_start, cm_thread_stop
from log import l

tt_n_elements = 1024 * 1024 * 2

def main():
	try:
		tt_init(tt_n_elements)

		board = chess.Board()

		while True:
			line = sys.stdin.readline()
			if line == None:
				break

			line = line.rstrip('\n')

			if len(line) == 0:
				continue

			l(line)

			parts = line.split(' ')
			
			if parts[0] == 'uci':
				print 'id name Feeks'
				print 'id author Folkert van Heusden <mail@vanheusden.com>'
				print 'uciok'

			elif parts[0] == 'isready':
				print 'readyok'

			elif parts[0] == 'ucinewgame':
				board = chess.Board()
				cm_thread_stop()

			elif parts[0] == 'position':
				is_moves = False
				nr = 1
				while nr < len(parts):
					if is_moves:
						board.push_uci(parts[nr])

					elif parts[nr] ==  'fen':
						board = chess.Board(' '.join(parts[nr + 1:]))
						break

					elif parts[nr] == 'startpos':
						board = chess.Board()

					elif parts[nr] == 'moves':
						is_moves = True

					else:
						l('unknown: %s' % parts[nr])

					nr += 1

			elif parts[0] == 'go':
				movetime = None
				depth = None
				wtime = btime = None
				winc = binc = None
				movestogo = None

				nr = 1
				while nr < len(parts):
					if parts[nr] == 'wtime':
						wtime = int(parts[nr + 1])
						nr += 1

					elif parts[nr] == 'btime':
						btime = int(parts[nr + 1])
						nr += 1

					elif parts[nr] == 'winc':
						winc = int(parts[nr + 1])
						nr += 1

					elif parts[nr] == 'binc':
						binc = int(parts[nr + 1])
						nr += 1

					elif parts[nr] == 'movetime':
						movetime = int(parts[nr + 1])
						nr += 1

					elif parts[nr] == 'movestogo':
						movestogo = int(parts[nr + 1])
						nr += 1

					elif parts[nr] == 'depth':
						depth = int(parts[nr + 1])
						nr += 1

					else:
						l('unknown: %s' % parts[nr])

					nr += 1

		###
				current_duration = movetime

				if current_duration:
					current_duration = float(current_duration) / 1000.0

				elif wtime and btime and winc and binc:
					ms = wtime
					time_inc = winc
					if not board.turn:
						ms = btime
						time_inc = binc

					ms /= 1000.0
					time_inc /= 1000.0

					if movestogo == None:
						movestogo = 40 - board.fullmove_number
						while movestogo < 0:
							movestogo += 40

					current_duration = (ms + movestogo * time_inc) / (board.fullmove_number + 7);

					limit_duration = ms / 15.0
					if current_duration > limit_duration:
						current_duration = limit_duration

					if current_duration == 0:
						current_duration = 0.001

					l('mtg %d, ms %f, ti %f' % (movestogo, ms, time_inc))
		###
				if current_duration:
					l('search for %f seconds' % current_duration)

				if depth == None:
					depth = 999

				cm_thread_stop()

				result = calc_move(board, current_duration, depth)
				if result and result[1]:
					print 'bestmove %s' % result[1].uci()
					board.push(result[1])

					cm_thread_start(board.copy())

				else:
					print 'bestmove a1a1'

			elif parts[0] == 'quit':
				break

			else:
				l('unknown: %s' % parts[0])

			sys.stdout.flush()

		cm_thread_stop()

	except KeyboardInterrupt as ki:
		l('ctrl+c pressed')
		cm_thread_stop()

	except Exception as ex:
		l(str(ex))
		l(traceback.format_exc())

#import cProfile
#cProfile.run('main()', 'restats')
main()
