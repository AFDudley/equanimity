from equanimity.unit_container import Container, Squad
from equanimity.units import Scient, Nescient
from equanimity.const import E, F, I, W, WEP_LIST
from ..base import create_comp, FlaskTestDB


class ContainerTest(FlaskTestDB):

    def setUp(self):
        super(ContainerTest, self).setUp()
        self.c = Container()
        self.s = Scient(E, create_comp(earth=128, fire=32, ice=32))
        self.nes = Nescient(E, create_comp(earth=128))

    def test_append(self):
        self.c.append(self.s)
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.c.free_spaces, 7)
        self.assertIn(self.s, self.c.units)
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
        self.c._update_value()
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
        self.c.append(self.nes)
        self.assertEqual(self.c.free_spaces, 5)
        self.assertEqual(self.c.value(), self.s.value() + self.nes.value())
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.s.container_pos, 0)
        self.assertEqual(self.nes.container_pos, 1)
        del self.c[0]
        self.assertEqual(self.c.free_spaces, 6)
        self.assertEqual(self.c.value(), self.nes.value())
        self.assertIs(self.s.container, None)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.nes.container_pos, 0)

    def test_remove(self):
        self.c.append(self.s)
        self.c.append(self.nes)
        self.assertEqual(self.c.free_spaces, 5)
        self.assertEqual(self.c.value(), self.s.value() + self.nes.value())
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.s.container_pos, 0)
        self.assertEqual(self.nes.container_pos, 1)
        self.c.remove(self.s)
        self.assertEqual(self.c.free_spaces, 6)
        self.assertEqual(self.c.value(), self.nes.value())
        self.assertIs(self.s.container, None)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.nes.container_pos, 0)
        self.assertRaises(ValueError, self.c.remove, self.s)

    def test_update_free_space_too_many_units(self):
        self.assertRaises(ValueError, Container, [self.s] * 20)

    def test_extend(self):
        s = Scient(E, create_comp(earth=128))
        self.c.extend([self.nes, s])
        self.assertEqual(self.c.free_spaces, 5)
        self.assertEqual(self.c.val, 256)
        self.assertEqual(self.c.units, [self.nes, s])

    def test_iadd(self):
        s = Scient(E, create_comp(earth=128))
        self.c += [self.nes, s]
        self.assertEqual(self.c.free_spaces, 5)
        self.assertEqual(self.c.val, 256)
        self.assertEqual(self.c.units, [self.nes, s])


class SquadTest(FlaskTestDB):

    def setUp(self):
        super(SquadTest, self).setUp()
        self.s = self._make_scient()
        self._squad = None

    def _make_scient(self):
        return Scient(E, {E: 128, F: 32, I: 32, W: 0})

    @property
    def squad(self):
        if self._squad is not None:
            return self._squad
        self._squad = Squad(name='x', data=[self._make_scient()])
        return self._squad

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
        self.assertEqual(self.squad.hp(), self.s.hp)

    def test_repr(self):
        msg = '<Squad x, Value: {0}, Free spaces: 7>'
        msg = msg.format(self.s.value())
        self.assertEqual(str(self.squad), msg)
        self.assertEqual(self.squad(), msg)

    def test_call(self):
        names = ['{0}: {1}'.format(i, t.name)
                 for i, t in enumerate(self.squad)]
        names = '\n'.join(names)
        msg = '<Squad x, Value: {val}, Free spaces: 7> \n{names}'
        msg = msg.format(val=self.s.value(), names=names)
        self.assertEqual(self.squad(more=True), msg)

    def test_add_to_stronghold(self):
        self.squad.add_to_stronghold('test', 777)
        self.assertEqual(self.squad.stronghold, 'test')
        self.assertEqual(self.squad.stronghold_pos, 777)

    def test_add_to_stronghold_while_queued(self):
        self.squad.queued_field = 10
        self.assertExceptionContains(
            ValueError, 'change queued squad\'s stronghold',
            self.squad.add_to_stronghold, 'test', 777
        )

    def test_remove_from_stronghold(self):
        self.test_add_to_stronghold()
        self.squad.remove_from_stronghold()
        self.assertIs(self.squad.stronghold, None)
        self.assertIs(self.squad.stronghold_pos, None)

    def test_remove_from_stronghold_while_queued(self):
        self.test_add_to_stronghold()
        self.squad.queued_field = 7
        self.assertExceptionContains(
            ValueError, 'change queued squad\'s stronghold',
            self.squad.remove_from_stronghold
        )

    def test_queue_at(self):
        self.squad.queue_at(7)
        self.assertEqual(self.squad.queued_field, 7)

    def test_unqueue(self):
        self.test_queue_at()
        self.squad.unqueue()
        self.assertIs(self.squad.queued_field, None)
