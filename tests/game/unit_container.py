from equanimity.unit_container import Container, Squad, MappedContainer
from equanimity.units import Scient, Nescient
from equanimity.const import E, F, I, W, WEP_LIST
from equanimity.helpers import AttributeDict
from ..base import create_comp, FlaskTestDB


class ContainerTest(FlaskTestDB):

    def setUp(self):
        super(ContainerTest, self).setUp()
        self.c = Container()
        self.s = Scient(E, create_comp(earth=128, fire=32, ice=32))
        self.t = Scient(E, create_comp(earth=64, fire=16, ice=16))
        self.nes = Nescient(E, create_comp(earth=128))

    def test_append(self):
        self.c.append(self.s)
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.c.size, 1)
        self.assertIn(self.s, self.c.units)
        self.assertEqual(self.s.value, self.s.value)
        self.assertFalse(self.c.full)

    def test_append_no_room(self):
        self.c.max_size = 1
        self.c.append(self.s)
        self.assertExceptionContains(ValueError, 'not enough space',
                                     self.c.append, self.t)

    def test_append_no_room_disabled(self):
        self.c.max_size = 0
        for i in range(100):
            self.c.append(Scient(E, create_comp(earth=128, fire=32, ice=32)))

    def test_value(self):
        self.assertEqual(self.c.value, 0)
        self.c.append(self.s)
        self.assertEqual(self.c.value, self.s.value)
        self.c.append(self.t)
        self.assertEqual(self.c.value, self.s.value + self.t.value)

    def test_setitem(self):
        self.assertEqual(self.c.value, 0)
        self.c.append(self.nes)
        self.assertEqual(self.c.value, self.nes.value)
        self.assertEqual(self.c.size, self.nes.size)
        self.assertEqual(self.nes.container, self.c)
        self.c[self.nes.container_pos] = self.nes
        self.assertEqual(len(self.c), 1)
        self.assertEqual(self.c[self.nes.container_pos], self.nes)
        self.assertEqual(self.c.value, self.nes.value)
        self.assertEqual(self.c.size, self.nes.size)
        self.assertEqual(self.nes.container, self.c)

    def test_setitem_no_overwrite(self):
        self.c.append(self.s)
        self.assertEqual(self.c.size, 1)
        self.assertFalse(self.c.full)
        self.assertExceptionContains(ValueError, 'Cannot overwrite existing',
                                     self.c.__setitem__, 0, self.nes)

    def test_delitem(self):
        self.c.append(self.s)
        self.c.append(self.nes)
        self.assertEqual(self.c.size, 3)
        self.assertEqual(self.c.value, self.s.value + self.nes.value)
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.s.container_pos, 0)
        self.assertEqual(self.nes.container_pos, 1)
        del self.c[0]
        self.assertEqual(self.c.size, 2)
        self.assertEqual(self.c.value, self.nes.value)
        self.assertIs(self.s.container, None)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.nes.container_pos, 0)

    def test_remove(self):
        self.c.append(self.s)
        self.c.append(self.nes)
        self.assertEqual(self.c.size, 3)
        self.assertEqual(self.c.value, self.s.value + self.nes.value)
        self.assertEqual(self.s.container, self.c)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.s.container_pos, 0)
        self.assertEqual(self.nes.container_pos, 1)
        self.c.remove(self.s)
        self.assertEqual(self.c.size, 2)
        self.assertEqual(self.c.value, self.nes.value)
        self.assertIs(self.s.container, None)
        self.assertEqual(self.nes.container, self.c)
        self.assertEqual(self.nes.container_pos, 0)
        self.assertRaises(ValueError, self.c.remove, self.s)

    def test_update_free_space_too_many_units(self):
        self.assertRaises(ValueError, Container, [self.s] * 20)

    def test_extend(self):
        s = Scient(E, create_comp(earth=128))
        self.c.extend([self.nes, s])
        self.assertEqual(self.c.size, 3)
        self.assertEqual(self.c.value, 256)
        self.assertEqual(self.c.units, [self.nes, s])

    def test_extend_no_room(self):
        self.c.max_size = 1
        s = Scient(E, create_comp(earth=128))
        self.assertExceptionContains(ValueError, 'not enough space',
                                     self.c.extend, [self.nes, s])
        self.assertEqual(len(self.c), 0)
        self.assertEqual(self.c.size, 0)
        self.assertEqual(self.c.value, 0)

    def test_extend_no_room_disabled(self):
        self.c.max_size = 0
        scients = [Scient(E, create_comp(earth=128)) for i in range(100)]
        self.c.extend(scients)
        self.assertEqual(self.c.size, len(scients) * Scient.size)
        self.assertEqual(self.c.value, scients[0].value * len(scients))
        self.assertEqual(self.c.units, scients)

    def test_iadd(self):
        s = Scient(E, create_comp(earth=128))
        self.c += [self.nes, s]
        self.assertEqual(self.c.size, 3)
        self.assertEqual(self.c.value, 256)
        self.assertEqual(self.c.units, [self.nes, s])


class MappedContainerTest(FlaskTestDB):

    def setUp(self):
        super(MappedContainerTest, self).setUp()
        self.m = MappedContainer()

    def _make_value(self, uid):

        class AttributeDictUID(AttributeDict):

            def __eq__(self, other):
                return self.uid == other.uid

            def __ne__(self, other):
                return not self.__eq__(other)

        return AttributeDictUID(uid=uid, size=1, value=lambda: 5,
                                remove_from_container=lambda: True,
                                add_to_container=lambda x, y: True)

    def test_create(self):
        self.assertTrue(hasattr(self.m, 'map'))
        self.assertEqual(len(self.m.map), len(self.m))

    def test_setitem_getitem_delitem(self):
        val = self._make_value(2)
        self.m[2] = val
        self.assertEqual(self.m[2], val)
        del self.m[2]
        self.assertRaises(KeyError, self.m.__getitem__, 2)

    def test_setitem_bad(self):
        self.assertRaises(KeyError, self.m.__setitem__, 2, self._make_value(3))

    def test_contains(self):
        val = self._make_value(7)
        self.m[7] = val
        self.assertIn(7, self.m)

    def test_get(self):
        val = self._make_value(7)
        self.m[7] = val
        self.assertIsNone(self.m.get(6))
        self.assertIsNone(self.m.get(8))
        self.assertEqual(self.m.get(8, default=0), 0)
        self.assertEqual(self.m.get(7), val)

    def test_append(self):
        val = self._make_value(7)
        self.m.append(val)
        self.assertIn(7, self.m)
        # reappend overwrites
        valx = self._make_value(7)
        self.m.append(valx)
        self.assertNotEqual(id(val), id(valx))
        self.assertEqual(id(self.m[7]), id(valx))

    def test_pop(self):
        val = self._make_value(7)
        self.m[7] = val
        r = self.m.pop(7)
        self.assertEqual(r, val)
        self.assertNotIn(7, self.m)
        self.assertNotIn(7, self.m.map)


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
        self.assertEqual(squad.value, self.s.value)
        self.assertEqual(squad.size, 1)

    def test_create_multiple_units(self):
        squad = Squad(name='x', data=[self.s, self._make_scient()])
        self.assertEqual(squad.name, 'x')
        self.assertEqual(squad.value, self.s.value * 2)
        self.assertEqual(squad.size, 2)

    def test_create_no_units_no_kind(self):
        squad = Squad(name='x')
        self.assertEqual(squad.name, 'x')
        self.assertEqual(squad.value, 0)
        self.assertEqual(squad.size, 0)
        self.assertFalse(squad.full)

    def test_create_no_units_kind_mins(self):
        self.assertRaises(Exception, Squad, kind='mins')
        squad = Squad(kind='mins', element='Earth')
        self.assertEqual(squad.name, 'Earth mins')
        self.assertEqual(len(squad), len(WEP_LIST))

    def test_hp(self):
        self.assertEqual(self.squad.hp(), self.s.hp)

    def test_repr(self):
        msg = '<Squad x, Value: {0}, Size: 1/8>'
        msg = msg.format(self.s.value)
        self.assertEqual(str(self.squad), msg)
        self.assertEqual(self.squad(), msg)

    def test_call(self):
        names = ['{0}: {1}'.format(i, t.name)
                 for i, t in enumerate(self.squad)]
        names = '\n'.join(names)
        msg = '<Squad x, Value: {val}, Size: 1/8> \n{names}'
        msg = msg.format(val=self.s.value, names=names)
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
