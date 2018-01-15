import chess
import copy

ht = []
ht_size = 1024
ht_sub_size = 8
q_hit = q_miss = 0

def init_board_ht():
    global ht, ht_size, ht_sub_size

    ht = [[[None, None] for i in xrange(ht_sub_size)] for i in xrange(ht_size)]

class Board(chess.Board, object):
	_moves = []

        __slots__ = [ '_moves' ]

	def _get_move_list(self, h):
                global ht, ht_size, ht_sub_size
                global q_hit, q_miss

		idx = h % ht_size

                for i in xrange(0, ht_sub_size):
                    if ht[idx][i][0] == h:
                            q_hit += 1

                            temp = ht[idx][i]
                            del ht[idx][i]
                            ht[idx].insert(0, temp)

                            return temp[1]

                q_miss += 1

		out = list(self.legal_moves)

                del ht[idx][-1]
                ht[idx].insert(0, [ h, out ])

		return out

	def get_move_list(self, h):
		return self._get_move_list(h)

	def move_count(self, h):
		return len(self._get_move_list(h))

        def get_stats(self):
                global q_hit, q_miss
                return { 'hit' : q_hit * 100.0 / (q_hit + q_miss) }
