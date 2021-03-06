from mock import MagicMock, Mock, patch, call
from unittest import TestCase
from voluptuous import Schema, Any
from operator import attrgetter
from equanimity.field import FieldQueue, Field
from equanimity.unit_container import Squad, rand_squad
from equanimity.player import Player
from equanimity.grid import Grid, Hex
from equanimity.battle import Battle
from equanimity.units import Scient
from equanimity.world import World
from equanimity.stone import Stone
from equanimity.const import FIELD_PRODUCE, FIELD_YIELD, FIELD_BATTLE, E, I
from equanimity.helpers import AttributeDict
from ..base import FlaskTestDB, FlaskTestDBWorld, create_comp


def _setup_full_queue():
    world = World()
    grid = Grid(radius=3)
    field = Field(world, (0, 0), I, grid=grid)
    return field, FieldQueue()


def _mocked_squad():
    mock_queue_at = Mock()
    return MagicMock(stronghold=MagicMock(location=Hex(0, 1)),
                     queue_at=mock_queue_at), mock_queue_at


class FieldQueueTestSimple(TestCase):

    def test_create(self):
        f = FieldQueue()
        self.assertFalse(f.queue)

    def test_flush(self):
        f = FieldQueue()
        f.queue[1] = 10
        self.assertTrue(f.queue)
        f.flush()
        self.assertFalse(f.queue)

    def test_pop(self):
        f = FieldQueue()
        self.assertIs(f.pop(), None)
        mock_unqueue = Mock()
        s = MagicMock(unqueue=mock_unqueue)
        f.queue[0] = s
        f.queue[1] = 'garbage'
        self.assertEqual(f.pop(), s)
        mock_unqueue.assert_called_once_with()


class FieldQueueTestDB(FlaskTestDB):

    def test_add(self):
        field, f = _setup_full_queue()
        s, mock_queue_at = _mocked_squad()
        f.add(field, s)
        mock_queue_at.assert_called_once_with(field)
        self.assertEqual(f.queue[Hex(0, 1)], s)

    def test_add_no_stronghold(self):
        field, f = _setup_full_queue()
        self.assertExceptionContains(ValueError, 'must be in a stronghold',
                                     f.add, field, Squad())

    def test_add_not_adjacent(self):
        field, f = _setup_full_queue()
        s = Squad()
        s.stronghold = AttributeDict(location=(0, 2))
        self.assertExceptionContains(ValueError, 'must be adjacent',
                                     f.add, field, s)

    def test_add_slot_taken(self):
        field, f = _setup_full_queue()
        s, _ = _mocked_squad()
        f.add(field, s)
        self.assertExceptionContains(ValueError, 'slot is taken', f.add,
                                     field, s)


class FieldWorldTest(FlaskTestDBWorld):

    """ Field tests that require a World """

    def setUp(self):
        super(FieldWorldTest, self).setUp(square_grid=False, grid_radius=3)

    def test_get_adjacent(self):
        f = self.world.fields[Hex(0, 0)]
        g = f.get_adjacent('Northeast')
        self.assertEqual(g.world_coord, Hex(1, -1))
        f = self.world.fields[Hex(self.world.grid.radius, 0)]
        # Off the edge of the map
        self.assertIsNone(f.get_adjacent('South'))


class FieldTest(FlaskTestDB):

    def setUp(self):
        super(FieldTest, self).setUp()
        self.player = Player('awcawca', 'a2@gmail.com', 'xcawcwaa')
        self.f = Field(AttributeDict(uid=1), (0, 0), I, owner=self.player)
        self.s = self.f.stronghold

    def test_create(self):
        self.assertEqual(self.f.world_coord, Hex(0, 0))
        self.assertEqual(self.f.owner, self.player)
        self.assertEqual(self.f.element, 'Ice')
        self.assertFalse(self.f.plantings)
        self.assertIs(self.f.battle, None)
        for x in ['grid', 'clock', 'stronghold', 'queue']:
            self.assertTrue(hasattr(self.f, x))

    def test_api_view(self):
        schema = Schema(dict(
            owner=int, element=str, coordinate=Hex, state=str,
            clock=dict, queue=[dict(uid=int, slot=[int, int])],
            battle=Any(None, int),
        ))
        self.assertValidSchema(self.f.api_view(), schema)

    def test_api_view_not_visible(self):
        requester = AttributeDict(get_visible_fields=lambda x: [])
        self.assertEqual(self.f.api_view(requester=requester), {})

    @patch('equanimity.field.get_world')
    def test_get(self, mock_get_world):
        fields = {tuple(self.f.world_coord): self.f}
        mock_get_world.return_value = AttributeDict(fields=fields)
        self.assertEqual(self.f, Field.get(0, (0, 0)))

    def test_in_battle(self):
        self.assertFalse(self.f.in_battle)
        self.f.battle = AttributeDict(state=AttributeDict(game_over=False))
        self.assertTrue(self.f.in_battle)
        self.f.battle = AttributeDict(state=AttributeDict(game_over=True))
        self.assertFalse(self.f.in_battle)

    def test_state(self):
        self.f.element = I
        self.assertEqual(self.f.state, FIELD_PRODUCE)
        self.f.element = E
        self.assertEqual(self.f.state, FIELD_YIELD)
        self.f.battle = AttributeDict(state=AttributeDict(game_over=False))
        self.assertEqual(self.f.state, FIELD_BATTLE)

    @patch('equanimity.player.get_world')
    def test_set_owner(self, mock_get_world):
        fields = {self.f.world_coord: self.f}
        mock_get_world.return_value = AttributeDict(fields=fields)
        wp = self.f.owner
        self.assertIn(self.f.world_coord, wp.get_fields(0))
        p = Player('x', 'x@gmail.com', 'xxx')
        self.f.owner = p
        self.assertIn(self.f.world_coord, p.get_fields(0))
        self.assertNotIn(self.f.world_coord, wp.get_fields(0))
        # make sure the free and squads and their units are updated
        self.s.silo.imbue(create_comp(earth=100))
        s = self.s.form_scient(E, create_comp(earth=1))
        t = self.s.form_scient(E, create_comp(earth=1))
        sq = self.s.form_squad(unit_ids=(t.uid,))
        self.assertEqual(s.owner, self.s.owner)
        self.assertEqual(t.owner, self.s.owner)
        self.assertEqual(sq.owner, self.s.owner)
        p = Player('xxdawda', 'fefe@gmail.com', 'asdwadawd')
        self.f.owner = p
        self.assertEqual(self.s.owner, p)
        self.assertEqual(s.owner, p)
        self.assertEqual(t.owner, p)
        self.assertEqual(sq.owner, self.s.owner)

    @patch('equanimity.stronghold.Stronghold.move_squad_in')
    @patch.object(Field, 'start_battle')
    def test_process_battle_and_movement_nothing_next(self, mock_battle,
                                                      mock_move):
        self.f.process_battle_and_movement()
        mock_battle.assert_not_called()
        mock_move.assert_not_called()

    @patch('equanimity.stronghold.Stronghold.move_squad_in')
    @patch.object(Field, 'start_battle')
    def test_process_battle_and_movement_restart_battle(self, mock_battle,
                                                        mock_move):
        opp = Player('awcawca', 'a2@gmail.com', 'xcawcwaa')
        k = Field(AttributeDict(uid=2), (0, 1), I, owner=opp)
        k.stronghold.silo.imbue(create_comp(earth=100))
        t = k.stronghold.form_scient(E, create_comp(earth=1))
        sq = k.stronghold.form_squad(unit_ids=(t.uid,))
        self.s.silo.imbue(create_comp(earth=100))
        self.s.form_scient(E, create_comp(earth=1))
        g = self.f.battle = Battle(self.f, sq)
        g.state.game_over = True
        self.f.process_battle_and_movement()
        mock_move.assert_not_called()
        mock_battle.assert_called_once_with(g.battlefield.atksquad)

    @patch('equanimity.stronghold.Stronghold.move_squad_in')
    def test_process_battle_and_movement_next_movement(self, mock_move):
        s, _ = _mocked_squad()
        s.owner = self.f.owner
        self.f.queue.add(self.f, s)
        self.f.process_battle_and_movement()
        mock_move.assert_called_once_with(s)

    @patch.object(Field, 'start_battle')
    def test_process_battle_and_movement_next_attacking(self, mock_start):
        s, _ = _mocked_squad()
        s.owner = None
        self.f.queue.add(self.f, s)
        self.f.process_battle_and_movement()
        mock_start.assert_called_once_with(s)

    @patch('equanimity.field.Battle.start')
    def test_start_battle(self, mock_start):
        sq = Squad()
        sq.owner = Player('t', 't@gmail.com', 'tttt')
        self.assertIs(self.f.battle, None)
        self.f.stronghold._setup_default_defenders()
        self.f.start_battle(sq)
        self.assertIsNot(self.f.battle, None)
        mock_start.assert_called_once_with()

    def test_place_scient_not_scient(self):
        self.assertExceptionContains(ValueError, 'must be a scient',
                                     self.f.place_scient, 1, (0, 0))

    def test_place_scient_not_positive(self):
        s = Scient(E, create_comp(earth=1))
        self.assertExceptionContains(
            ValueError, 'First coordinate of location must be positive',
            self.f.place_scient, s, (0, 0))
        self.assertExceptionContains(
            ValueError, 'First coordinate of location must be positive',
            self.f.place_scient, s, (-1, 0))

    def test_place_scient_not_in_squad(self):
        s = Scient(E, create_comp(earth=1))
        self.assertExceptionContains(ValueError, 'must be in a squad',
                                     self.f.place_scient, s, (1, 0))

    def test_place_scient_not_on_grid(self):
        s = Scient(E, create_comp(earth=1))
        Squad(data=[s])
        self.assertExceptionContains(ValueError, 'does not fit',
                                     self.f.place_scient, s, (100, 0))

    def test_place_scient_no_collision(self):
        s = Scient(E, create_comp(earth=1))
        t = Scient(E, create_comp(earth=1))
        Squad(data=[s, t])
        self.f.place_scient(s, (1, 0))
        self.assertExceptionContains(ValueError, 'already occupied',
                                     self.f.place_scient, t, (1, 0))

    def test_place_scient(self):
        s = Scient(E, create_comp(earth=1))
        Squad(data=[s])
        self.f.place_scient(s, (1, 0))
        self.assertEqual(s.chosen_location, Hex(1, 0))

    @patch('equanimity.field.WorldPlayer.get')
    def test_eq(self, mock_get):
        mock_get.return_value = None
        self.assertEqual(self.f, self.f)
        # non matching coords
        self.assertNotEqual(self.f, Field(self.f.world, (1, 0), I))
        # non matching world
        self.f.world = 0
        self.assertNotEqual(self.f, Field(1, self.f.world_coord, I))
        # non matching type
        self.assertNotEqual(self.f, 1)

    @patch('equanimity.silo.Silo.imbue_list')
    @patch('equanimity.field.Field.get_taken_over')
    @patch('equanimity.stronghold.Stronghold.add_free_unit')
    @patch('equanimity.field.Field.check_ungarrisoned')
    def test_battle_end_attacker_wins(self, mock_garr, mock_add, mock_taken,
                                      mock_imbue):
        # Update with attacker wins
        atksquad = rand_squad(size=4)
        defsquad = rand_squad(size=4)
        winner = atksquad
        prisoners = [u for u in defsquad]
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        self.f.battle_end_callback(atksquad, defsquad, winner, awards,
                                   prisoners)
        mock_garr.assert_called_once_with()
        mock_add.assert_not_called()
        mock_taken.assert_called_once_with(atksquad)
        mock_imbue.assert_called_once_with(awards)

    @patch('equanimity.silo.Silo.imbue_list')
    @patch('equanimity.field.Field.get_taken_over')
    @patch('equanimity.stronghold.Stronghold.add_free_unit')
    @patch('equanimity.field.Field.check_ungarrisoned')
    def test_battle_end_defender_wins(self, mock_garr, mock_add, mock_taken,
                                      mock_imbue):
        # Update with defender wins
        atksquad = rand_squad(size=4)
        defsquad = rand_squad(size=4)
        winner = defsquad
        prisoners = [u for u in atksquad]
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        self.f.battle_end_callback(atksquad, defsquad, winner, awards,
                                   prisoners)
        mock_garr.assert_called_once_with()
        prisoners = sorted(prisoners, key=attrgetter('value'),
                           reverse=True)
        mock_add.assert_has_calls([call(u) for u in prisoners])
        mock_taken.assert_not_called()
        mock_imbue.assert_called_once_with(awards)

    @patch('equanimity.silo.Silo.imbue_list')
    @patch('equanimity.field.Field.get_taken_over')
    @patch('equanimity.stronghold.Stronghold.add_free_unit')
    @patch('equanimity.field.Field.check_ungarrisoned')
    def test_battle_end_defender_wins_stronghold_full(self, mock_garr,
                                                      mock_add, mock_taken,
                                                      mock_imbue):
        # Update with defender wins
        mock_add.side_effect = ValueError
        atksquad = rand_squad(size=4)
        defsquad = rand_squad(size=4)
        winner = defsquad
        prisoners = [u for u in atksquad]
        awards = [Stone(create_comp(earth=2, ice=3, fire=1, wind=7))]
        self.f.battle_end_callback(atksquad, defsquad, winner, awards,
                                   prisoners)
        mock_garr.assert_called_once_with()
        prisoner = None
        for p in prisoners:
            if prisoner is None or p.value > prisoner.value:
                prisoner = p
        self.assertIsNotNone(prisoner)
        mock_add.assert_called_once_with(prisoner)
        mock_taken.assert_not_called()
        mock_imbue.assert_called_once_with(awards)
