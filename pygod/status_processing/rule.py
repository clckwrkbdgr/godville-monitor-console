import logging

class Rule:
    '''
    Class describing how to process dictinary item
    '''

    def __init__(self, condition, action, check_active=False, ignore_first_result=False):
        self.condition = condition
        self.action = action
        self.ignore_first_result = ignore_first_result
        self.check_active = check_active
        self._last_result = False

    def check(self, hero_state):
        if self.check_active and hero_state.get('expired', False):
            logging.debug('Hero state is expired, will not check rule.')
            return

        try:
            result = self.condition(hero_state)
        except Exception as e:
            logging.error('%s: exception in condition: %s',
                          self.check.__name__,
                          str(e))
            return None

        run_action = True
        if self.ignore_first_result:
            logging.debug('Ignoring first result')
            self.ignore_first_result = False
            run_action = False

        if self._last_result != result:
            self._last_result = result
            if result and run_action:
                try:
                    self.action()
                except Exception as e:
                    logging.error('%s: exception in action: %s',
                                  self.check.__name__,
                                  str(e))
            return result

        return None
