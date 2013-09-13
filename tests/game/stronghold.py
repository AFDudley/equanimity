from equanimity.grid import Hex
from equanimity.world import World
from equanimity.unit_container import Squad
from equanimity.stronghold import Stronghold
from ..base import FlaskTestDB, _scient


class StrongholdTest(FlaskTestDB):

    def setUp(self):
        super(StrongholdTest, self).setUp()
        self.w = World()
        self.w.create()
        self.f = self.db['fields'][Hex(0, 0)]
        self.s = self.f.stronghold

    def test_create(self):
        self.assertEqual(self.s.owner, self.f.owner)
        self.assertEqual(self.s.field, self.f)
        self.assertEqual(self.s.clock, self.f.clock)
        self.assertIs(self.s.stable, None)
        self.assertIs(self.s.armory, None)
        self.assertIs(self.s.farm, None)
        self.assertIsNot(self.s.home, None)

    def test_units(self):
        scients = [_scient(earth=77), _scient(earth=99)]
        for s in scients:
            self.s.free_units.append(s)
        sq_scients_a = [_scient(earth=111)]
        sq_scients_b = [_scient(earth=32), _scient(earth=64)]
        self.s.squads.append(Squad(data=sq_scients_a))
        self.s.squads.append(Squad(data=sq_scients_b))
        scients = scients + sq_scients_a + sq_scients_b
        for s in scients:
            self.assertIn(s, self.s.units)

    def test_get(self):
        loc = Hex(0, 1)
        s = Stronghold.get(loc)
        self.assertTrue(s)
        self.assertEqual(s.field.world_coord, loc)

    def test_create_factory(self):
        # Maps attribute_name -> kinds
        c = dict(stable=['Stable', 'Earth'],
                 armory=['Armory', 'Fire'],
                 home=['Home', 'Ice'],
                 farm=['Farm', 'Wind'])

        # Clear anything set
        for key in c:
            # might as well check this...
            self.assertTrue(hasattr(self.s, key))
            setattr(self.s, key, None)

        for key, kinds in c.iteritems():
            for kind in kinds:
                # Setting once should be correct
                self.assertIs(getattr(self.s, key), None)
                self.s.create_factory(kind)
                self.assertIsNot(getattr(self.s, key), None)
                # Setting again should raise ValueError mentioning the kind
                self.assertExceptionContains(ValueError, kinds[0].lower(),
                                             self.s.create_factory, kind)
                # Reset
                setattr(self.s, key, None)

        # Invalid kind
        self.assertExceptionContains(ValueError, 'Unknown',
                                     self.s.create_factory, 'sdamdwadm')
