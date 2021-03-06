from mock import patch, Mock, MagicMock, call
from unittest import TestCase
from datetime import timedelta, datetime
from equanimity.clock import WorldClock, FieldClock
from equanimity.const import CLOCK, ELEMENTS, E, F, FIELD_PRODUCE, FIELD_YIELD
from equanimity.helpers import AttributeDict
from ..base import BaseTest, FlaskTestDBWorld


class WorldClockTest(BaseTest):

    def test_create(self):
        w = WorldClock()
        self.assertEqual(sorted(CLOCK.keys()), sorted(w._current.keys()))
        for v in w._current.values():
            self.assertEqual(v, 1)

    @patch('equanimity.clock.now')
    @patch.object(WorldClock, 'get_current_state')
    def test_create_dob(self, mock_state, mock_now):
        mock_now.return_value = 777
        w = WorldClock()
        self.assertEqual(w.dob, 777)

    @patch('equanimity.clock.now')
    @patch.object(WorldClock, 'get_current_state')
    def test_elapsed(self, mock_state, mock_now):
        _now = datetime.now()
        mock_now.return_value = _now
        w = WorldClock()
        mock_now.return_value = _now + timedelta(minutes=1)
        self.assertEqual(w.elapsed, 60)

        # test in the past error handling
        mock_now.return_value = _now
        w = WorldClock()
        mock_now.return_value = _now - timedelta(minutes=1)
        self.assertEqual(w.elapsed, 0)

    @patch.object(WorldClock, '_get_interval_value')
    def test_game_over(self, mock_interval):
        w = WorldClock()
        mock_interval.return_value = 1
        self.assertFalse(w.game_over)
        mock_interval.return_value = 2
        self.assertTrue(w.game_over)

    @patch.object(WorldClock, 'get_current_state')
    @patch.object(WorldClock, 'change_day')
    @patch.object(WorldClock, 'change_season')
    def test_tick(self, mock_change_season, mock_change_day, mock_get_state):
        # check that current gets updated
        ret = dict(day=1, season=1)
        mock_get_state.return_value = ret
        w = WorldClock()
        f = 1
        w.tick(f)
        self.assertEqual(ret, w._current)
        # check that change_day gets called
        ret = dict(day=2, season=2)
        mock_get_state.return_value = ret
        w.tick(f)
        mock_change_season.assert_called_once_with(f)
        mock_change_day.assert_called_once_with(f)
        self.assertEqual(ret, w._current)

    @patch.object(WorldClock, 'elapsed')
    def test_get_interval_value(self, mock_elapsed):
        elapsed = int(timedelta(hours=70).total_seconds())
        mock_elapsed.__get__ = Mock(return_value=elapsed)
        w = WorldClock()
        self.assertEqual(w._get_interval_value('season'), 9)

    def test_getattribute(self):
        w = WorldClock()
        # CLOCK key attr
        for k in CLOCK:
            self.assertEqual(getattr(w, k), 1)
        # other attr
        self.assertTrue(w.dob)

    def test_setattr(self):
        w = WorldClock()
        w.xxx = 777
        self.assertEqual(w.xxx, 777)
        self.assertExceptionContains(ValueError, 'Can\'t set', w.__setattr__,
                                     'day', 7)


class WorldClockTestDB(FlaskTestDBWorld):

    def setUp(self):
        super(WorldClockTestDB, self).setUp()
        self.w = WorldClock()

    @patch('equanimity.field.FieldClock.change_day')
    def test_change_day(self, mock_change):
        fields = self.world.fields
        self.w.change_day(fields)
        mock_change.assert_has_calls([call(f) for f in fields.values()])

    @patch('equanimity.field.FieldClock.change_season')
    def test_change_season(self, mock_change):
        fields = self.world.fields
        self.w.change_season(fields)
        mock_change.assert_has_calls([call() for f in fields.values()])


class FieldClockTest(TestCase):

    def test_create(self):
        f = FieldClock()
        self.assertEqual(f.season, E)
        f = FieldClock(season=F)
        self.assertEqual(f.season, F)

    def test_state(self):
        f = FieldClock()
        self.assertEqual(f.state(AttributeDict(element=E)), FIELD_YIELD)
        f = FieldClock()
        self.assertEqual(f.state(AttributeDict(element=F)), FIELD_PRODUCE)

    def test_change_season(self):
        f = FieldClock()
        self.assertEqual(f.season, E)
        for i, e in enumerate(ELEMENTS[1:] + (ELEMENTS[0],)):
            f.change_season()
            self.assertEqual(f.season, e)

    def test_change_day(self):
        mock_process = Mock()
        f = FieldClock()
        field = MagicMock(in_battle=False,
                          process_battle_and_movement=mock_process)
        f.change_day(field)
        mock_process.assert_called_once_with()

    def test_change_day_in_battle(self):
        mock_process = Mock()
        f = FieldClock()
        field = MagicMock(in_battle=True,
                          process_battle_and_movement=mock_process)
        f.change_day(field)
        mock_process.assert_not_called()
