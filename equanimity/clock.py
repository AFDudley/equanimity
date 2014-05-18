"""
clock.py

Created by AFD on 2013-08-05.
Copyright (c) 2013 A. Frederick Dudley. All rights reserved.
"""
from persistent import Persistent
from helpers import now, timestamp
from const import CLOCK, ELEMENTS, E, FIELD_PRODUCE, FIELD_YIELD


"""
Global world clock -
    -- keeps track of time? (or does external method trigger it on time)
    -- advances the clocks of each field

Field clock:
    -- season
    -- time since birth, in pretty format
    -- on tick, just update season
"""


class WorldClock(Persistent):

    def __init__(self):
        self.dob = now()
        self._current = self.get_current_state()

    def api_view(self):
        return dict(dob=timestamp(self.dob),
                    elapsed=self.elapsed,
                    state=self.get_current_state())

    @property
    def elapsed(self):
        e = int((now() - self.dob).total_seconds())
        # Handle time error margins that can cause this to be negative:
        return max(0, e)

    @property
    def game_over(self):
        return self.generation > 1

    def get_current_state(self):
        """ Returns the current computed clock interval values since dob """
        return {k: getattr(self, k) for k in CLOCK}

    def tick(self, fields):
        """ Updates the clock state, and does necessary actions if the
        day or season changes.
        Call this at least once per game day (4 minutes).

        When this function is called, it will advance clocks if enough time
        has elapsed.  Otherwise no action occurs
        """

        '''
        TODO -- this assumes the tick() will not skip any days
        i.e. the process that calls this on time is not down, and there is
        not a recurrent Exception being raised in this function's call stack

        How should we handle that failure?
            -- Consider the game paused
            -- Fill in any missing days with default actions
                (Might cause unpredictable results from a player's pov)
        '''
        next = self.get_current_state()
        if next['day'] > self._current['day']:
            self.change_day(fields)
        if next['season'] > self._current['season']:
            self.change_season(fields)
        self._current = next

    def change_day(self, fields):
        for field in fields.values():
            print "FROM CLOCK.PY: changing day to {} on Field {} in world {}".format(self._current['day'], field.world_coord, field.world.uid)
            field.clock.change_day(field)

    def change_season(self, fields):
        for field in fields.values():
            field.clock.change_season()

    def _get_interval_value(self, interval):
        return 1 + (self.elapsed // int(CLOCK[interval].total_seconds()))

    def __getattribute__(self, k):
        """ Computes day, week, year, season, generation on demand
        """
        s = super(WorldClock, self)
        if k in CLOCK:
            return s.__getattribute__('_get_interval_value')(k)
        else:
            return s.__getattribute__(k)

    def __setattr__(self, k, v):
        if k in CLOCK:
            raise ValueError('Can\'t set {0}'.format(k))
        super(WorldClock, self).__setattr__(k, v)


class FieldClock(Persistent):

    def __init__(self, season=E):
        self.season = season

    def state(self, field):
        if self.season == field.element:
            return FIELD_YIELD
        else:
            return FIELD_PRODUCE

    def change_day(self, field):
        """ Process the field's queues """
        if field.in_battle:
            # We can't process the next queued action until that battle
            # is resolved. When that battle completes, it will trigger the
            # next action
            return
        # Do the next battle or movement
        field.process_battle_and_movement()
        # Revert to the WorldPlayer if left empty
        field.check_ungarrisoned()

    def change_season(self):
        """ Move to the next season """
        next = (ELEMENTS.index(self.season) + 1) % len(ELEMENTS)
        self.season = ELEMENTS[next]

    def api_view(self):
        return dict(season=self.season)
