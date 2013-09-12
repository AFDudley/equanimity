from persistent import Persistent


class AutoID(Persistent):
    def __init__(self, name=''):
        super(AutoID, self).__init__()
        self.name = name
        self.uid = 0

    def get_next_id(self):
        self.uid += 1
        return self.uid

    def __str__(self):
        return u'<AutoID {name} [{uid}]>'.format(name=self.name, uid=self.uid)
