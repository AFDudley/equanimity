from mock import MagicMock, Mock, patch
from unittest import TestCase
from voluptuous import Schema
from equanimity.field import FieldQueue, Field
from equanimity.unit_container import Squad
from equanimity.player import Player
from equanimity.grid import Grid, Hex
from equanimity.units import Scient
from equanimity.const import FIELD_PRODUCE, FIELD_YIELD, FIELD_BATTLE, E, I
from server.utils import AttributeDict
from ..base import FlaskTestDB, create_comp


def _setup_full_queue():
    grid = Grid(radius=3)
    field = Field((0, 0), grid=grid)
    return FieldQueue(field)


def _mocked_squad():
    mock_queue_at = Mock()
    return MagicMock(stronghold=MagicMock(location=Hex(0, 1)),
                     queue_at=mock_queue_at), mock_queue_at


class FieldQueueTestSimple(TestCase):

    def test_create(self):
        f = FieldQueue(1)
        self.assertEqual(f.field, 1)
        self.assertFalse(f.queue)

    def test_flush(self):
        f = FieldQueue(None)
        f.queue[1] = 10
        self.assertTrue(f.queue)
        f.flush()
        self.assertFalse(f.queue)

    def test_pop(self):
        f = FieldQueue(None)
        self.assertIs(f.pop(), None)
        mock_unqueue = Mock()
        s = MagicMock(unqueue=mock_unqueue)
        f.queue[0] = s
        f.queue[1] = 'garbage'
        self.assertEqual(f.pop(), s)
        mock_unqueue.assert_called_once_with()


class FieldQueueTestDB(FlaskTestDB):

    def test_add(self):
        f = _setup_full_queue()
        s, mock_queue_at = _mocked_squad()
        f.add(s)
        mock_queue_at.assert_called_once_with(f.field)
        self.assertEqual(f.queue[Hex(0, 1)], s)

    def test_add_no_stronghold(self):
        f = FieldQueue(None)
        self.assertExceptionContains(ValueError, 'must be in a stronghold',
                                     f.add, Squad())

    def test_add_not_adjacent(self):
        f = _setup_full_queue()
        s = Squad()
        s.stronghold = AttributeDict(location=(0, 2))
        self.assertExceptionContains(ValueError, 'must be adjacent',
                                     f.add, s)

    def test_add_slot_taken(self):
        f = _setup_full_queue()
        s, _ = _mocked_squad()
        f.add(s)
        self.assertExceptionContains(ValueError, 'slot is taken', f.add, s)


class FieldTest(FlaskTestDB):

    def setUp(self):
        super(FieldTest, self).setUp()
        self.player = Player('awcawca', 'a2@gmail.com', 'xcawcwaa')
        self.f = Field((0, 0), owner=self.player)

    def test_create(self):
        self.assertEqual(self.f.world_coord, Hex(0, 0))
        self.assertEqual(self.f.owner, self.player)
        self.assertEqual(self.f.element, 'Ice')
        self.assertFalse(self.f.plantings)
        self.assertIs(self.f.game, None)
        for x in ['grid', 'clock', 'stronghold', 'queue']:
            self.assertTrue(hasattr(self.f, x))

    def test_api_view(self):
        schema = Schema(dict(
            owner=int, element=str, coordinate=Hex, state=str,
            clock=dict
        ))
        self.assertValidSchema(self.f.api_view(), schema)

    def test_api_view_not_visible(self):
        requester = AttributeDict(visible_fields=[])
        self.assertEqual(self.f.api_view(requester=requester), {})

    def test_get(self):
        self.db['fields'] = dict()
        self.db['fields'][tuple(self.f.world_coord)] = self.f
        self.assertEqual(self.f, Field.get((0, 0)))

    def test_in_battle(self):
        self.assertFalse(self.f.in_battle)
        self.f.game = AttributeDict(state=dict(game_over=False))
        self.assertTrue(self.f.in_battle)
        self.f.game = AttributeDict(state=dict(game_over=True))
        self.assertFalse(self.f.in_battle)

    def test_state(self):
        self.f.element = I
        self.assertEqual(self.f.state, FIELD_PRODUCE)
        self.f.element = E
        self.assertEqual(self.f.state, FIELD_YIELD)
        self.f.game = AttributeDict(state=dict(game_over=False))
        self.assertEqual(self.f.state, FIELD_BATTLE)

    def test_set_owner(self):
        wp = self.f.owner
        self.assertIn(self.f.world_coord, wp.fields)
        p = Player('x', 'x@gmail.com', 'xxx')
        self.f.owner = p
        self.assertIn(self.f.world_coord, p.fields)
        self.assertNotIn(self.f.world_coord, wp.fields)

    def test_process_queue_nothing_next(self):
        self.assertIs(self.f.process_queue(), None)

    @patch('equanimity.stronghold.Stronghold.move_squad_in')
    def test_process_queue_next_movement(self, mock_move):
        s, _ = _mocked_squad()
        s.owner = self.f.owner
        self.f.queue.add(s)
        self.assertEqual(self.f.process_queue(), s)
        mock_move.assert_called_once_with(s)

    @patch.object(Field, 'start_battle')
    def test_process_queue_next_attacking(self, mock_start):
        s, _ = _mocked_squad()
        s.owner = None
        self.f.queue.add(s)
        self.assertEqual(self.f.process_queue(), s)
        mock_start.assert_called_once_with(s)

    @patch('equanimity.field.Game.start')
    def test_start_battle(self, mock_start):
        sq = Squad()
        Player('t', 't@gmail.com', 'tttt', squads=[sq])
        self.assertIs(self.f.game, None)
        self.f.stronghold._setup_default_defenders()
        self.f.start_battle(sq)
        self.assertIsNot(self.f.game, None)
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

    def test_eq(self):
        self.assertEqual(self.f, self.f)
        self.assertNotEqual(self.f, Field((1, 0)))
        self.assertNotEqual(self.f, 1)
