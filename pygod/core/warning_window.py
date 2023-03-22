import logging
import curses
from .text_entry import TextEntry
from .text_entry import Colors
from .monitor_window import MonitorWindowBase
from ..core.utils import tr

class WarningWindow(MonitorWindowBase):
    def __init__(self,
                 parent_window,
                 text):

        self._text = [' ' + line + ' ' for line in text.splitlines()]
        self._last_line = tr('Press SPACE...')

        # Include borders to window size
        width  = max(max(map(len, self._text)), len(self._last_line)) + 2
        height = 4 + len(self._text)

        (max_y, max_x) = parent_window.getmaxyx()

        y = int((max_y - height)/2)
        x = int((max_x - width)/2)

        if (x < 0 or y < 0):
            logging.error('%s: Text is too long \'%s\'',
                          self.__init__.__name__,
                          self._text)
            x = 0
            y = 0
            width = min(width, max_x - 1)
            height = min(height, max_y - 1)
            self._text = [line[:width] - 2 for line in self._text[:height - 4]]

        super(WarningWindow, self).__init__(parent_window, tr('Warning'), x, y, width, height)

        self.window.bkgd(' ', curses.color_pair(Colors.ATTENTION))

    def init_text_entries(self):
        for line in self._text:
            self.text_entries.append(TextEntry(line, '', self.width, Colors.ATTENTION))
        self.text_entries.append(TextEntry('', '', self.width, Colors.ATTENTION))
        self.text_entries.append(TextEntry(self._last_line, '', self.width, Colors.ATTENTION))
