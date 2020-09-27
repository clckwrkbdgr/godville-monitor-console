import logging

class Rule:
    '''
    Class describing how to process dictinary item
    '''

    def __init__(self, condition, action, ignore_first_result=False):
        self.condition = condition
        self.action = action
        self.ignore_first_result = ignore_first_result
        self._last_result = False

    def check(self, hero_state):
        try:
            result = self.condition(hero_state)
        except Exception as e:
            logging.error('%s: exception in condition: %s',
                          self.check.__name__,
                          str(e))
            return None

        if self._last_result != result:
            self._last_result = result
            if result:
                if self.ignore_first_result:
                    self.ignore_first_result = False
                    return None
                try:
                    self.action()
                except Exception as e:
                    logging.error('%s: exception in action: %s',
                                  self.check.__name__,
                                  str(e))
            return result

        return None
