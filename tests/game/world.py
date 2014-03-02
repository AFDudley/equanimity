from mock import patch, call
from equanimity.world import World
from equanimity.player import Player
from equanimity.const import ELEMENTS, ORTH, OPP, I
from ..base import FlaskTestDB


class WorldTest(FlaskTestDB):

    def test_get(self):
        w = World.create()
        x = World.get(w.uid)
        self.assertEqual(w, x)

    @patch.object(World, '_create_fields')
    def test_create(self, mock_persist):
        World.create()
        mock_persist.assert_called_once_with()

    @patch.object(World, '_create_fields')
    def test_init(self, mock_create):
        World(create_fields=False)
        mock_create.assert_not_called()
        World(create_fields=True)
        mock_create.assert_called_once_with()

    @patch.object(World, '_populate_fields')
    @patch.object(World, '_distribute_fields_to_players')
    def test_start(self, mock_dist, mock_pop):
        w = World()
        w.start()
        mock_dist.assert_called_once_with()
        mock_pop.assert_called_once_with()

    def test_award_field_not_participating(self):
        w = World()
        loc = (0, 0)
        p = Player('xxx', 'xxx@example.com', 'xxxpassword')
        self.assertExceptionContains(ValueError, "Not participating",
                                     w.award_field, p, loc)

    def test_award_field(self):
        w = World()
        loc = (0, 0)
        self.assertEqual(w.player, w.fields[loc].owner)
        p = Player('xxx', 'xxx@example.com', 'xxxpassword')
        w.players.add(p)
        w.award_field(p, loc)
        self.assertEqual(p, w.fields[loc].owner)

    def test_persist(self):
        w = World()
        self.assertIsNone(self.db['worlds'].get(w.uid))
        w.persist()
        self.assertEqual(self.db['worlds'][w.uid], w)

    @patch('equanimity.stronghold.Stronghold.populate')
    def test_populate_fields_no_players(self, mock_populate):
        w = World()
        w._populate_fields()
        mock_populate.assert_has_calls([call(kind=None) for x in w.fields])

    @patch('equanimity.stronghold.Stronghold.populate')
    def test_populate_fields(self, mock_populate):
        w = World()
        p = Player('xxx', 'xxx@example.com', 'xxxpassword')
        for f in w.fields.itervalues():
            f.owner = p
        w._populate_fields()
        mock_populate.assert_has_calls([call(kind='Scient') for x in w.fields])

    def test_choose_initial_field_element(self):
        w = World()
        for i in range(100):
            self.assertIn(w._choose_initial_field_element((0, 0)), ELEMENTS)

    def test_choose_initial_field_grid(self):
        w = World()
        for i in range(100):
            g = w._choose_initial_field_grid(I, (0, 0))
            for x in ORTH[I]:
                self.assertGreaterEqual(g.comp[I], g.comp[x])
                self.assertGreaterEqual(g.comp[x], g.comp[OPP[I]])
            self.assertEqual(g.radius, w.grid.radius)

    @patch.object(World, '_choose_initial_field_grid')
    @patch.object(World, '_choose_initial_field_element')
    def test_create_fields(self, mock_elem, mock_grid):
        w = World(create_fields=False)
        mock_elem.return_value = I
        grid = w._choose_initial_field_grid(I, (0, 0))
        mock_grid.return_value = grid
        self.assertEqual(len(w.fields), 0)
        w._create_fields()
        self.assertEqual(len(list(w.grid.iter_coords())), len(w.fields))
        for c, f in w.fields.iteritems():
            self.assertTrue(w.grid.in_bounds(c))
            self.assertEqual(f.world_coord, c)
            self.assertEqual(f.element, I)
            self.assertEqual(f.grid, grid)
            self.assertEqual(w.player, f.owner)
        mock_elem.assert_has_calls([call(c) for c in w.grid.iter_coords()])
        mock_grid.assert_has_calls([call(I, c) for c in w.grid.iter_coords()])

    def test_distribute_fields_to_players_one_player(self):
        w = World()
        p = Player('xxx', 'xxx@example.com', 'xxxpassword')
        w.players.add(p)
        w._distribute_fields_to_players()
        for f in w.fields.itervalues():
            self.assertEqual(f.owner, p)


class WorldTestRealGrid(FlaskTestDB):

    """ Uses a hex grid with a nontrivial radius """

    def setUp(self):
        super(WorldTestRealGrid, self).setUp(grid_radius=4, square_grid=False)

    def test_distribute_fields_to_players_two_players(self):
        w = World()
        p = Player('xxx', 'xxx@example.com', 'xxxpassword')
        q = Player('yyy', 'yyy@example.com', 'yyypassword')
        w.players.add(p)
        w.players.add(q)
        self.assertEqual(len(w.grid), len(list(w.grid.iter_coords())))
        self.assertEqual(len(w.grid) % 2, 1)
        w._distribute_fields_to_players()
        pf = [f for f in w.fields.itervalues() if f.owner == p]
        qf = [f for f in w.fields.itervalues() if f.owner == q]
        self.assertEqual(len(pf), len(qf))
        self.assertEqual(len(pf) + len(qf) + 1, len(w.fields))
