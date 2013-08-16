from base import FlaskTest
from equanimity.player import Player


class PlayerTest(FlaskTest):

    def test_get_player_bad_uid(self):
        player = Player.get('xxx')
        self.assertIs(player, None)
