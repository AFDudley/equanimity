from equanimity.unit_container import Container, Squad
from equanimity.units import Scient, Nescient
from equanimity.const import E, F, I, W, WEP_LIST
from base import create_comp, FlaskTestDB


class ContainerTest(FlaskTestDB):

    def setUp(self):
        super(ContainerTest, self).setUp()
        self.c = Container()
        self.s = Scient(E, create_comp(earth=128, fire=32, ice=32))
        self.nes = Nescient(E, create_comp(earth=128))

    def test_unit_size(self):
        self.assertRaises(TypeError, self.c.append, object())
        self.assertEqual(self.c.unit_size(self.s), 1)
        self.assertEqual(self.c.unit_size(self.nes), 2)

    def test_append(self):
        self.c.append(self.s)
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.c.free_spaces, 7)
        self.assertIn(self.s, self.c.data)
        self.assertEqual(self.c.val, self.s.value())

    def test_append_no_room(self):
        self.c.free_spaces = 0
        self.assertRaises(Exception, self.c.append, self.s)

    def test_value(self):
        self.assertEqual(self.c.value(), self.c.val)

    def test_update_value(self):
        self.c.append(self.s)
        val = self.c.val
        self.assertNotEqual(val, 0)
        self.c.val = 0
        self.c.update_value()
        self.assertEqual(self.c.val, val)

    def test_setitem(self):
        self.c.append(self.nes)
        self.assertEqual(self.nes.container, self.c)
        self.c[0] = self.s
        self.assertEqual(self.c[0], self.s)
        self.assertEqual(self.c.val, self.s.value())
        self.assertEqual(self.c.free_spaces, 7)
        self.assertEqual(self.s.container, self.c)
        self.assertIs(self.nes.container, None)

    def test_setitem_no_space(self):
        self.c.free_spaces = 1
        self.c.append(self.s)
        self.assertEqual(self.c.free_spaces, 0)
        self.assertRaises(Exception, self.c.__setitem__, 0, self.nes)

    def test_delitem(self):
        self.c.append(self.s)
        self.assertEqual(self.c.free_spaces, 7)
        self.assertEqual(self.c.value(), self.s.value())
        self.assertEqual(self.s.container, self.c)
        del self.c[0]
        self.assertEqual(self.c.free_spaces, 8)
        self.assertEqual(self.c.value(), 0)
        self.assertIs(self.s.container, None)


class SquadTest(FlaskTestDB):

    def _make_scient(self):
        return Scient(E, {E: 128, F: 32, I: 32, W: 0})

    def setUp(self):
        super(SquadTest, self).setUp()
        self.s = self._make_scient()

    def test_create_single_unit(self):
        squad = Squad(name='x', data=self.s)
        self.assertEqual(squad.name, 'x')
        self.assertEqual(squad.value(), self.s.value())
        self.assertEqual(squad.free_spaces, 7)

    def test_create_multiple_units(self):
        squad = Squad(name='x', data=[self.s, self._make_scient()])
        self.assertEqual(squad.name, 'x')
        self.assertEqual(squad.value(), self.s.value() * 2)
        self.assertEqual(squad.free_spaces, 6)

    def test_create_no_units_no_kind(self):
        squad = Squad(name='x')
        self.assertEqual(squad.name, 'x')
        self.assertEqual(squad.value(), 0)
        self.assertEqual(squad.free_spaces, 8)

    def test_create_no_units_kind_mins(self):
        self.assertRaises(Exception, Squad, kind='mins')
        squad = Squad(kind='mins', element='Earth')
        self.assertEqual(squad.name, 'Earth mins')
        self.assertEqual(len(squad), len(WEP_LIST))

    def test_hp(self):
        squad = Squad(data=[self.s])
        self.assertEqual(squad.hp(), self.s.hp)

    def test_repr(self):
        s = Squad(name='x', data=[self.s])
        msg = 'Name: x, Value: {0}, Free spaces: 7 \n'
        msg = msg.format(self.s.value())
        self.assertEqual(str(s), msg)
        self.assertEqual(s(), msg)

    def test_call(self):
        s = Squad(name='x', data=[self.s])
        names = ['{0}: {1}'.format(i, t.name) for i, t in enumerate(s)]
        names = '\n'.join(names)
        msg = 'Name: x, Value: {val}, Free spaces: 7 \n{names}'
        msg = msg.format(val=self.s.value(), names=names)
        self.assertEqual(s(more=True), msg)
