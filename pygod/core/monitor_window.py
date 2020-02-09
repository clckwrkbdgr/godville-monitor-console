from .text_entry import TextEntry
from .text_entry import ListEntry
from .text_entry import Colors
import logging
import curses
import textwrap

class MonitorWindowBase:
    '''
    Base class for all windows of the Godville Monitor

    '''
    def __init__(self, parent_window, title, x=0, y=0, width=None, height=None):
        self.title        = title
        self.text_entries = []

        parent_height, parent_width = parent_window.getmaxyx()

        self.x           = x
        self.y           = y
        self.width       = width if width else parent_width - x
        self.height      = height if height else parent_height - y
        self.window      = parent_window.subwin(self.height,
                                                 self.width,
                                                 self.y,
                                                 self.x)
        self.window.box()
        self.init_text_entries()

    def add_text_entry(self, entry, key=None, width=None, color=None):
        if key is None:
            self.text_entries.append(entry)
        else:
            self.text_entries.append(TextEntry(entry, key,
                width if width is not None else self.width,
                color if color is not None else Colors.STANDART))

    def add_list_entry(self, list_generator, width=None, color=None):
        self.text_entries.append(ListEntry(list_generator,
            width if width is not None else self.width,
            color if color is not None else Colors.STANDART))

    def update(self, state):
        logging.debug('%s: Updating window \'%s\'',
                      self.update.__name__,
                      self.title)

        self.window.erase()
        self.window.box()
        self.window.addstr(0, 2, self.title)

        for entry in self.text_entries:
            entry.update(state)

        self.write_text(self.text_entries)
        self.window.refresh()

    def init_text_entries(self):
        pass

    def split_text(self, text, length):
        if not text:
            return ['']
        return textwrap.wrap(text, length)

    def write_text_chunks(self, chunks, color, start_line):
        for i, chunk in enumerate(chunks):
            try:
                self.window.addnstr(start_line + i,
                                    1,
                                    chunk,
                                    self.width - 2,
                                    curses.color_pair(color))
            except curses.error as e:
                if 'addnwstr() returned ERR' in str(e):
                    self.window.box()
                    self.window.addstr(0, 2, self.title)
                    self.window.addnstr(self.height - 2, self.width - 7, '[...]', 5, curses.color_pair(Colors.ATTENTION))


    def write_text(self, entries):
        offset = 1 # Offset for correcting line number for splitted text

        for i, entry in enumerate(entries):
            if isinstance(entry.text, str):
                logging.debug('%s: Writting text \'%s\'',
                              self.write_text.__name__,
                              entry.text)
                chunks = self.split_text(entry.text, self.width - 2)
                self.write_text_chunks(chunks, entry.color, i + offset)
                offset += len(chunks) - 1
            else:
                for line, color in entry.text:
                    chunks = self.split_text(line, self.width - 2)
                    self.write_text_chunks(chunks, color, i + offset)
                    offset += len(chunks) - 1
                    offset += 1
