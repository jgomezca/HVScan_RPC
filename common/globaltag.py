class GTTypeNotDetected(Exception):
    '''Raised when Global Tag object tries to detect onw type and fails'''
    pass

class GlobalTag(object):

    # map between relval process and GT type
    RELVALMAP = dict() #getWfList
    RELVALMAP['mc'] = ['29', '35']
    RELVALMAP['ideal'] = ['29', '35']
    RELVALMAP['startup'] = ['29', '35']
    RELVALMAP['hlt'] = ['4.291']
    RELVALMAP['data'] = ['4.17']
    RELVALMAP['cosmics'] = ['4.22']
    RELVALMAP['hi'] = ['40', '41', '42']
    RELVALMAP['express'] = ['4.17']
    RELVALMAP['prompt'] = ['1000', '4.17']

    def __init__(self, name, gt_type):
        '''If gt_type is none - doing autodetection'''
        self._name = str(name)
        self._type = gt_type

        if self._type is None:
            self._detect_gt_type()

        self._detect_gt_options()

    def _detect_gt_type(self):
        # determine the type from the GT name
        if "_H_" in self._name:
            self._type = 'hlt'
        elif "DESIGN" in self._name:
            self._type = 'ideal'
        elif "MC" in self._name:
            self._type = 'mc'
        elif "STARTHI" in self._name:
            self._type = 'hi'
        elif "START" in self._name:
            self._type = 'startup'
        elif "GR_R" in self._name or "FT" in self._name:
            self._type = 'data'
        elif "CRFT" in self._name or "CRAFT" in self._name:
            self._type = 'cosmics'
        elif "GR_E_" in self._name:
            self._type = 'express'
        elif "GR_P_" in self._name:
            self._type = 'prompt'
        elif "POST" in self._name:
            self._type = 'mc'

        else:
            raise GTTypeNotDetected("Could not detect gt type for " + self._name)

    def _detect_gt_options(self):
        self._is_online = (self._type == 'hlt')
        self._is_monte_carlo = (self._type == 'ideal') or\
                               (self._type == 'startup') or\
                               (self._type == 'mc') or\
                               (self._type == 'hi')


    @property
    def name(self):
        return self._name

    @property
    def isOnline(self):
        return self._is_online

    @property
    def isMC(self):
        return self._is_monte_carlo

    @property
    def relval(self):
        return self.RELVALMAP[self._type]

    @property
    def type(self):
        return self._type