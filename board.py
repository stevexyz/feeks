import chess
import copy

ht = []
ht_size = 1024
ht_sub_size = 8
q_hit = q_miss = 0

def init_board_ht():
    global ht, ht_size, ht_sub_size

    ht = [[[None, None] for i in range(ht_sub_size)] for i in range(ht_size)]

class Board(chess.Board, object):
    def _get_move_list(self, h):
        global ht, ht_size, ht_sub_size
        global q_hit, q_miss

        idx = h % ht_size

        for i in range(0, ht_sub_size):
            if ht[idx][i][0] == h:
                q_hit += 1

                if i:
                    ht[idx].insert(0, ht[idx].pop(i))

                return ht[idx][0][1]

        q_miss += 1

        return None

    def _put_move_list(self, h):
        global ht, ht_size

        idx = h % ht_size

        out = list(self.legal_moves)

        del ht[idx][-1]
        ht[idx].insert(0, [ h, out ])

        return out

    def get_move_list(self, h):
        out = self._get_move_list(h)

        if not out:
            out = self._put_move_list(h)

        return out

    def move_count(self, h):
        return len(self.get_move_list(h))

    def get_stats(self):
        global q_hit, q_miss
        return { 'hit' : q_hit * 100.0 / (q_hit + q_miss) }
