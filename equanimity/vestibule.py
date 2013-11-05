from persistent import Persistent
from world import World, PlayerGroup
from server import db


class Vestibule(Persistent):
    """ A game waiting for players to start
    """

    @classmethod
    def get(self, uid):
        return db['vestibules'].get(self.uid)

    def __init__(self):
        self.players = PlayerGroup()
        self.uid = db['vestibule_uid'].get_next_id()

    def api_view(self):
        return dict(players=[p for p in self.players], uid=self.uid)

    def persist(self):
        db['vestibules'][self.uid] = self

    def start(self):
        """ Create a World for these players """
        w = World()
        w.players.add_all(self.players)
        w.persist()
        w.start()
        del db['vestibules'][self.uid]
        return w
