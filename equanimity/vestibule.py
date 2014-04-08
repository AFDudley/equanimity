from persistent import Persistent
from world import World, PlayerGroup
from server import db


class Vestibule(Persistent):

    """ A game waiting for players to start
    """

    @classmethod
    def get(self, uid):
        return db['vestibules'].get(uid)

    def __init__(self):
        self.players = PlayerGroup()
        self.uid = db['vestibule_uid'].get_next_id()
        self.world = None

    def api_view(self):
        leader = self.players.get_leader()
        if leader is not None:
            leader = leader.uid
        world = self.world
        if world is not None:
            world = getattr(self.world, 'uid', self.world)
        return dict(players=[p.uid for p in self.players], uid=self.uid,
                    leader=leader, world=world)

    def persist(self):
        db['vestibules'][self.uid] = self

    def start(self):
        """ Create a World for these players """
        w = World.create()
        w.players.add_all(self.players.players.values())
        w.start()
        self.world = w.uid
        return w

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.uid == other.uid

    def __ne__(self, other):
        return not self.__eq__(other)
