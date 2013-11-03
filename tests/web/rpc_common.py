from server.rpc.common import get_battle
from battle import BattleTestBase


class TestGetBattle(BattleTestBase):

    def test_bad_battle_participant(self):
        self._start_battle()
        self.game.defender = self.game.attacker  # short circuit
        self.assertRaises(ValueError, get_battle, self.world.uid, (0, 0))
