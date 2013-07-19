from twython import TwythonStreamer
import curses
import textwrap

class StreamCatcher(TwythonStreamer):
	def start(self):
		self.lines = []
		self.linewrap = textwrap.TextWrapper()
		try:
			self.stdscr = curses.wrapper(self._run)
		except KeyboardInterrupt:
			self.disconnect()

	def _run(self, screen):
		curses.start_color()
		curses.use_default_colors()
		curses.echo()
		self.nrows, self.ncols = screen.getmaxyx()
		self.linewrap.width = self.ncols
		self._screen = screen
		self._addline('=> Connected!')
		self.user(replies=all)

	def _addline(self, line):
		# First part sanitizes input for the screen - break input buffer into lines
		# (\n), then into screen lines based on width
		line = line.rstrip()
		actuallines = line.split("\n")
		for entry in actuallines:
			screenlines = self.linewrap.wrap(entry)
			for item in screenlines:
				self.lines.append(item)
		# Now we clear the screen and loop over the formatted lines to display them.
		self._screen.clear()
		i = 0;
		index = len(self.lines) - 1
		while i < self.nrows - 2 and index >= 0:
			self._screen.addstr(self.nrows-2-i, 0, self.lines[index])
			i = i + 1
			index = index - 1
		self._screen.move(self.nrows-1, 0)
		self._screen.refresh()

	def on_success(self, data):
		if 'text' in data:
			self._addline(data['user']['name'].encode('utf-8') + ' [' + data['user']['screen_name'].encode('utf-8') + ']: ' + data['text'].encode('utf-8'))
		elif 'friends' in data:
			num = len(data['friends'])
			self._addline('=> You are following ' + str(num) + ' user' + ('' if num == 1 else 's'))
		else:
			self._addline('Received: ' + str(data))

	def on_error(self, status_code, data):
		self.addline('ERR: [' + status_code + '] ' + data)
