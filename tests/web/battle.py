from equanimity.battle import Battle
from equanimity.units import Scient
from equanimity.unit_container import Squad
from equanimity.weapons import Bow
from equanimity.player import Player
from equanimity.grid import Hex
from equanimity.const import E
from ..base import create_comp
from rpc_base import RPCTestBase


class BattleTestBase(RPCTestBase):

    def setUp(self, **db_kwargs):
        super(BattleTestBase, self).setUp(**db_kwargs)
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
        self.battle = Battle(self.f, atksquad)
        self.battle.persist()
        self.f.battle = self.battle

    def _start_battle(self):
        s, t, atks, defs = self._create_units()
        self._setup_game(atks, defs)
        return s, t, atks, defs


class BattleTest(BattleTestBase):

    service_name = 'battle'

    def test_invalid_field(self):
        r = getattr(self.proxy, 'pass')(self.world.uid, (66, 77), 1)
        self.assertError(r, 'Invalid Field')

    def test_field_not_in_battle_game_over(self):
        s, t, atksquad, defsquad = self._create_units()
        self._setup_game(atksquad, defsquad)
        self.f.battle.state.game_over = True
        r = getattr(self.proxy, 'pass')(self.world.uid, self.loc, 1)
        self.assertError(r, 'No game is active for this field')

    def test_field_not_in_battle_not_started(self):
        self.f.battle = None
        r = getattr(self.proxy, 'pass')(self.world.uid, self.loc, 1)
        self.assertError(r, 'No game is active for this field')

    def test_pass(self):
        s, t, atksquad, defsquad = self._create_units()
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(1, 0))
        self.f.place_scient(t, Hex(1, 0))
        self.battle.start()
        r = getattr(self.proxy, 'pass')(self.world.uid, self.loc, t.uid)
        self.assertNoError(r)

    def test_move(self):
        s, t, atksquad, defsquad = self._create_units()
        self._setup_game(atksquad, defsquad)
        self.f.place_scient(s, Hex(1, 0))
        self.f.place_scient(t, Hex(1, 0))
        self.battle.start()
        self._setup_game(atksquad, defsquad)
        r = self.proxy.move(self.world.uid, self.loc, t.uid, Hex(2, 0))
        self.assertNoError(r)


class BattleTestBiggerGrid(BattleTestBase):

    service_name = 'battle'

    def setUp(self):
        super(BattleTestBiggerGrid, self).setUp(grid_radius=6)

    def test_attack(self):
        s, t, atksquad, defsquad = self._create_units()
        wep = Bow(E, create_comp(earth=0))
        t.equip(wep)
        self._setup_game(atksquad, defsquad)
        print 'Radius:', self.f.grid.radius
        self.f.place_scient(s, Hex(2, 4))
        self.f.place_scient(t, Hex(1, 1))
        self.battle.start()
        self._setup_game(atksquad, defsquad)
        r = self.proxy.attack(self.world.uid, self.loc, t.uid, Hex(-2, -4))
        self.assertNoError(r)
