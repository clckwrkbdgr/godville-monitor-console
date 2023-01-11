import curses
from ..core import MonitorWindowBase
from ..core import TextEntry
from ..core import Colors
import datetime
from ..core.utils import tr

def _session_state(state):
    if 'error' in state:
        return state['error'], Colors.ATTENTION
    if 'token_expired' in state:
        return tr('Token expired'), Colors.ATTENTION
    if 'expired' in state:
        return tr('Expired'), Colors.ATTENTION
    return tr('Active'), None

def session_state(state):
    return _session_state(state)[0]

def session_state_color(state):
    return _session_state(state)[1]

def item_priority(item):
    if 'activate_by_user' in item and item['activate_by_user']:
        return 3
    if item['price'] > 0:
        return 2
    if 'type' in item and item['type'] == 'heal_potion':
        return 1
    return 0

def inventory_list(state):
    # New api replaced inventory with 'activatables' list.
    if 'activatables' in state:
        for item in state['activatables']:
            yield '- {0}'.format(item), Colors.POWER_POINTS
        return
    inventory = state['inventory']
    item_list = []
    for item_name in inventory:
        item_state = inventory[item_name]
        item_state['name'] = item_name
        item_list.append(item_state)
    item_list.sort(key=lambda item: item['pos'])
    item_list.sort(key=item_priority, reverse=True)
    for item in item_list:
        color = None
        if 'activate_by_user' in item and item['activate_by_user']:
            color = Colors.POWER_POINTS
        elif 'type' in item and item['type'] == 'heal_potion':
            color = Colors.HEALING
        elif item['price'] > 0:
            color = Colors.MONEY
        if item['cnt'] > 1:
            yield '- {0} (x{1})'.format(item['name'], item['cnt']), color
        else:
            yield '- {0}'.format(item['name']), color

DIARY_EVENTS = [] # (timestamp, text)
def diary_events(state):
    global DIARY_EVENTS
    last_entry = state['diary_last']
    if not DIARY_EVENTS or last_entry != DIARY_EVENTS[0][1]:
        DIARY_EVENTS.insert(0, (datetime.datetime.now(), last_entry))
    DIARY_EVENTS = DIARY_EVENTS[:10]
    return [('{0}  {1}'.format(timestamp.strftime('%H:%M'), entry), None) for (timestamp, entry) in DIARY_EVENTS]

def hero_location(state):
    if 'arena_fight' in state and state['arena_fight']:
        if 'fight_type' in state:
            return state['fight_type']
        else:
            return tr('Fight!')
    else:
        if 'town_name' in state and state['town_name']:
            return state['town_name']
    return tr('{0} pl').format(state['distance'])

def creatures_in_ark(state):
    if 'ark_completed_at' not in state or not state['ark_completed_at']:
        return '-'
    return '{0}m, {1}f'.format(state['ark_m'], state['ark_f'])

def building_state(state, building_name, item_name, always_show_items=False):
    done = state.get('{0}_completed_at'.format(building_name))
    if not done:
        return ''
    item_cnt = '{0}%'.format(state['{0}_cnt'.format(item_name)]/10.0)
    if done:
        if always_show_items:
            return tr('done ({0})').format(item_cnt)
        else:
            return tr('done')
    return item_cnt

def pet_state(state):
    if 'pet' not in state:
        return '-'
    level = state['pet']['pet_level']
    if 'wounded' in state['pet']:
        level = str(level) + tr('(hurt)')
    return level

def pet_caption(state):
    if 'pet' not in state:
        return ''
    pet = state['pet']
    result = ''
    if 'pet_class' in pet:
        result += pet['pet_class'] + ' '
    result += pet['pet_name']
    return result

class MainWindow(MonitorWindowBase):
    def __init__(self, stdscr):
        (height, width) = stdscr.getmaxyx()
        super(MainWindow, self).__init__(stdscr, '')

        self._subwindows = []

        # TODO: t_level and savings_completed_at
        # Column 1: Main hero stats.
        windows = [
                (tr('Session'), [
                    ('', session_state, session_state_color),
                    ]),
                (tr('God'), [
                    ('', 'godname'),
                    (tr('Power:'), 'godpower', Colors.POWER_POINTS),
                    ]),
                (tr('Hero'), [
                    ('', 'name'),
                    ('', 'alignment'),
                    (tr('HP:'), lambda state: '{0}/{1}'.format(state['health'], state['max_health']), Colors.HEALTH_POINTS),
                    (tr('Lvl:'), lambda state: '{0} ({1}%)'.format(state['level'], state['exp_progress'])),
                    (tr('Arena:'), lambda state: '{0}/{1}'.format(state['arena_won'], state['arena_lost'])),
                    (tr('Clan:'), lambda state: '{0}, {1}'.format(state['clan'], state['clan_position'])),
                    (),
                    (tr('Location:'), hero_location),
                    (),
                    (tr('Aura:'), lambda state: state['aura'] if 'aura' in state else ''),
                    ]),
                (tr('Temple'), [
                    (tr('Temple:'), lambda state: building_state(state, 'temple', 'bricks')),
                    (tr('Savings:'), lambda state: state['savings'] if 'savings' in state else ''),
                    ]),
                (tr('Ark'), [
                    (tr('Ark:'), lambda state: building_state(state, 'ark', 'wood', always_show_items=True)),
                    (tr('Beasts:'), creatures_in_ark),
                    ]),
                (tr('Pet'), [
                    ('', pet_caption),
                    (),
                    (tr('Level:'), pet_state),
                    ]),
                ]

        current_column_size = 0
        for window_name, window_entries in windows:
            wnd = MonitorWindowBase(self.window, window_name, 0, current_column_size, 22, 2 + len(window_entries))
            for entry in window_entries:
                if not entry:
                    continue # Just a space or placeholder for unexpected events.
                if len(entry) > 2:
                    wnd.add_text_entry(entry[0], entry[1], color=entry[2])
                else:
                    wnd.add_text_entry(entry[0], entry[1])
            self._subwindows.append(wnd)
            current_column_size += 2 + len(window_entries)
        if height > current_column_size:
            wnd = MonitorWindowBase(self.window, '', 0, current_column_size, 22, None)
            self._subwindows.append(wnd)

        # Column 2: Inventory.
        wnd = MonitorWindowBase(self.window, tr('Inventory'), 22, 0, 30, None)
        wnd.add_text_entry(tr('Gold:'), 'gold_approx')
        wnd.add_text_entry(tr('Items:'), lambda state: '{0}/{1}'.format(state['inventory_num'], state['inventory_max_num']))
        wnd.add_list_entry(inventory_list)
        self._subwindows.append(wnd)

        # Column 3: Quest, diary etc.
        wnd = MonitorWindowBase(self.window, tr('Log'), 52, 0, None, None)
        wnd.add_text_entry(tr('Quest: '), lambda state: '{0} ({1}%)'.format(state['quest'], state['quest_progress']))
        wnd.add_text_entry('', '')
        wnd.add_text_entry('', lambda state: '"{0}"'.format(state['motto']))
        wnd.add_text_entry('', lambda x: '* * *')
        wnd.add_list_entry(diary_events)
        self._subwindows.append(wnd)

    def update(self, state):
        super(MainWindow, self).update(state)
        for window in self._subwindows:
            window.update(state)

        self.window.refresh()

