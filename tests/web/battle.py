from equanimity.battle import Game
from equanimity.units import Scient
from equanimity.unit_container import Squad
from equanimity.weapons import Bow
from equanimity.player import Player
from equanimity.grid import Hex
from equanimity.const import E
from ..base import create_comp
from rpc_base import RPCTestBase


class BattleTestBase(RPCTestBase):

    def setUp(self):
        super(BattleTestBase, self).setUp()
        self.defender = self.get_user()
        self.f.owner = self.defender
        self.attacker = Player('Atk', 'x@gmail.com', 'xxx')

    def _create_units(self):
        s = Scient(E, create_comp(earth=2))
        atksquad = Squad(data=[s])
        t = self.f.stronghold.form_scient(E, create_comp(earth=1))
        defsquad = self.f.stronghold.form_squad(unit_ids=(t.uid,))
        return s, t, atksquad, defsquad

    def _setup_game(self, atksquad, defsquad):
        atksquad.owner = self.attacker
        defsquad.owner = self.defender
        self.game = Game(self.f, atksquad)
        self.f.game = self.game

    def _start_battle(self):
        s, t, atks, defs = self._create_units()
        self._setup_game(atks, defs)
        return s, t, atks, defs


class BattleTest(BattleTestBase):

    service_name = 'battle'

    def test_invalid_field(self):
        r = getattr(self.proxy, 'pass')((66, 77), 1)
        self.assertError(r, 'Invalid Field')

    def test_field_not_in_battle_game_over(self):
        s, t, atksquad, defsquad = self._create_units()
        self._setup_game(atksquad, defsquad)
        self.f.game.state['game_over'] = True
        r = getattr(self.proxy, 'pass')(self.loc, 1)
        self.assertError(r, 'No game is active for this field')

    def test_field_not_in_battle_not_started(self):
        self.f.game = None
        r = getattr(self.proxy, 'pass')(self.loc, 1)
        self.assertError(r, 'No game is active for this field')

    def test_pass(self):
        s, t, atksquad, defsquad = self._create_units()
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(1, 0))
        self.f.place_scient(t, Hex(1, 0))
        self.game.start()
        r = getattr(self.proxy, 'pass')(self.loc, t.uid)
        self.assertNoError(r)

    def test_move(self):
        s, t, atksquad, defsquad = self._create_units()
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(1, 0))
        self.f.place_scient(t, Hex(1, 0))
        self.game.start()
        self._setup_game(atksquad, defsquad)
        r = self.proxy.move(self.loc, t.uid, Hex(2, 0))
        self.assertNoError(r)

    def test_attack(self):
        s, t, atksquad, defsquad = self._create_units()
        wep = Bow(E, create_comp(earth=0))
        t.equip(wep)
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(2, 4))
        self.f.place_scient(t, Hex(1, 1))
        self.game.start()
        self._setup_game(atksquad, defsquad)
        r = self.proxy.attack(self.loc, t.uid, Hex(-2, -4))
        self.assertNoError(r)
