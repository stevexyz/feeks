import chess

class Board(chess.Board):
	_moves = []

	def _get_move_list(self):
		out = []

		for m in self.legal_moves:
			out.append(m)

		return out

	def get_move_list(self):
		if not self._moves:
			self._moves.append(self._get_move_list())

		return self._moves[-1]

	def move_count(self):
		return len(self.get_move_list())

	def push(self, m):
		super(Board, self).push(m)

		self._moves.append(self._get_move_list())

	def pop(self):
                del self._moves[-1]

		return super(Board, self).pop()

	def _set_lists(self, lists):
		self._moves = lists

	def _clear(self):
		self._moves = []

	def copy(self):
		c = super(Board, self).copy()
		c._clear()
		return c

	def get_stats(self):
		return { 'len' : len(self._moves) }
