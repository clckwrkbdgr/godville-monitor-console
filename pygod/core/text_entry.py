import logging
from ..core.utils import tr

class Colors:
    STANDART        = 1
    HEALTH_POINTS   = 2
    POWER_POINTS    = 3
    ATTENTION       = 4
    MONEY       = 5
    HEALING       = 6


class TextEntry:
    def __init__(self, predefined_text, key, width, color = Colors.STANDART):
        self.predefined_text = predefined_text
        self.key             = key
        self.width           = width
        self.color           = color
        self.attribute       = None
        self.text            = ''

    def update(self, state, attribute = None):
        logging.debug('%s: Updating entry \'%s\'',
                       self.update.__name__,
                       self.predefined_text)

        key_width   = self.width - len(self.predefined_text) - 2
        custom_text = ''
        text_format = '{0}{1:>{2}}'

        if isinstance(self.key, str) and self.key == '' and self.predefined_text == '':
            self.text = ''
            return

        # In case of empty predefined text use center alignment
        if self.predefined_text == '':
            text_format = '{0}{1:^{2}}'
        elif isinstance(self.key, str) and self.key == '':
            text_format = '{0:^{2}}'

        if not isinstance(self.key, str):
            custom_text = self.key(state)
            if custom_text is None:
                custom_text = tr('N/A')
        elif self.key != '':
            try:
                custom_text = '{0}'.format(state[self.key])
            except KeyError:
                logging.warning('%s: Key not found \'%s\'',
                                self.update.__name__,
                                self.key)
                custom_text = tr('N/A')

        if key_width < 0:
            self.text = tr("{0} text doesn't fit").format(self.key)
            return

        self.text = text_format.format(self.predefined_text,
                                        custom_text,
                                        key_width)

class ListEntry:
    def __init__(self, list_generator, width, color = Colors.STANDART):
        self.generator = list_generator
        self.width           = width
        self.color           = color
        self.text            = []

    def update(self, state):
        self.text = []
        for item, color in self.generator(state):
            if color is None:
                color = Colors.STANDART
            self.text.append( (item, color) )

