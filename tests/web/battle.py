from equanimity.battle import Game
from equanimity.units import Scient
from equanimity.unit_container import Squad
from equanimity.weapons import Bow
from equanimity.player import Player
from equanimity.grid import Hex
from equanimity.const import E
from ..base import create_comp
from rpc_base import RPCTestBase


class BattleTest(RPCTestBase):

    def setUp(self):
        super(BattleTest, self).setUp()
        self.defender = self.get_user()
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx')

    def _setup_game(self, atksquad, defsquad):
        self.attacker.squads = [atksquad]
        self.defender.squads = [defsquad]
        self.game = Game(self.f, self.attacker, self.defender)
        self.f.game = self.game

    def test_invalid_field(self):
        r = getattr(self.proxy, 'pass')((66, 77), 1)
        self.assertError(r, 'Invalid Field')

    def test_pass(self):
        s = Scient(E, create_comp(earth=2))
        t = Scient(E, create_comp(earth=1))
        atksquad = Squad(data=[s])
        defsquad = Squad(data=[t])
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(1, 0))
        self.f.place_scient(t, Hex(1, 0))
        self.game.put_squads_on_field()
        r = getattr(self.proxy, 'pass')(self.loc, t.uid)
        self.assertNoError(r)

    def test_move(self):
        s = Scient(E, create_comp(earth=2))
        t = Scient(E, create_comp(earth=1))
        atksquad = Squad(data=[s])
        defsquad = Squad(data=[t])
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(1, 0))
        self.f.place_scient(t, Hex(1, 0))
        self.game.put_squads_on_field()
        self._setup_game(atksquad, defsquad)
        r = self.proxy.move(self.loc, t.uid, Hex(2, 0))
        self.assertNoError(r)

    def test_attack(self):
        s = Scient(E, create_comp(earth=2))
        t = Scient(E, create_comp(earth=1))
        wep = Bow(E, create_comp(earth=0))
        t.equip(wep)
        atksquad = Squad(data=[s])
        defsquad = Squad(data=[t])
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(2, 4))
        self.f.place_scient(t, Hex(1, 1))
        self.game.put_squads_on_field()
        self._setup_game(atksquad, defsquad)
        r = self.proxy.attack(self.loc, t.uid, Hex(-2, -4))
        self.assertNoError(r)
