from voluptuous import Schema, Any
from battle import BattleTestBase


class InfoTest(BattleTestBase):

    service_name = 'info'

    def setUp(self):
        super(InfoTest, self).setUp()
        self._setup_schemas()

    def _setup_schemas(self):
        self.clock_schema = Schema(dict(clock=dict(dob=int, elapsed=int,
                                                   state=dict)))
        self._field_clock_schema = dict(season=unicode)
        self._field_schema = dict(
            owner=int, element=unicode, coordinate=[int, int], state=unicode,
            clock=self._field_clock_schema
        )
        self.field_schema = Schema(dict(field=self._field_schema))
        self.world_schema = Schema(dict(
            world=dict(uid=int, visible_fields=[self._field_schema])
        ))
        self._battle_timer_schema = dict(
            start_time=int, action_num=int, current_ply=int, current_unit=int,
            time_remaining=int
        )
        self.battle_timer_schema = Schema(dict(
            battle=dict(timer=self._battle_timer_schema)
        ))
        self._unit_schema = dict(
            comp=dict, element=unicode, name=unicode, location=list,
            dob=unicode, dod=None, uid=int, chosen_location=list, size=int,
            weapon=dict, weapon_bonus=dict, equip_limit=dict,
            sex=unicode, move=int
        )
        self.unit_schema = Schema(dict(unit=self._unit_schema))
        self._combatant_squad_schema = dict(
            name=unicode, owner=int, units=[self._unit_schema]
        )
        self.combatant_schema = Schema(dict(
            username=unicode, uid=int, squad=self._combatant_squad_schema
        ))
        self.battle_schema = Schema(dict(battle=dict(
            timer=self._battle_timer_schema, defender=self.combatant_schema,
            attacker=self.combatant_schema, action_num=int
        )))
        self._squad_schema = Schema(dict(
            name=unicode, units=[int], stronghold=list,
            stronghold_pos=Any(None, int), queued_field=Any(None, int)
        ))
        self._silo_schema = Schema(dict(comp=dict, limit=dict))
        self.stronghold_schema = Schema(dict(stronghold=dict(
            field=list, silo=self._silo_schema, weapons=[dict],
            free_units=[self._unit_schema], squads=[self._squad_schema],
            defenders=self._squad_schema
        )))

    def _coerce(self, expect):
        """ Convert expected api_view data to the types that will be received
        over json (I don't know why its bitching about comparing unicode to
        nonunicode """
        data = {}
        for k, v in expect.iteritems():
            if isinstance(k, basestring):
                k = unicode(k)
            if isinstance(v, basestring):
                v = unicode(v)
            elif isinstance(v, tuple):
                v = list(v)
            elif isinstance(v, dict):
                v = self._coerce(v)
            if isinstance(v, list):
                _v = []
                for x in v:
                    if isinstance(x, dict):
                        x = self._coerce(x)
                    _v.append(x)
                v = _v
            data[k] = v
        return data

    def _test(self, name, *args, **kwargs):
        r = getattr(self.proxy, name)(*args, **kwargs)
        self.assertNoError(r)
        schema = getattr(self, name + '_schema')
        self.assertValidSchema(r['result'], schema)
        return r['result']

    def test_world_info(self):
        self._test('world', self.world.uid)

    def test_field_info(self):
        data = self._test('field', self.world.uid, self.loc)
        expect = self._coerce(self.field.api_view())
        self.assertEqual(expect, data['field'])

    def test_clock_info(self):
        self._test('clock', self.world.uid)

    def test_battle_info(self):
        self.maxDiff = None
        self._start_battle()
        data = self._test('battle', self.world.uid, self.loc)
        expect = self._coerce(self.field.game.api_view())
        self.assertEqual(expect, data['battle'])

    def test_battle_timer_info(self):
        self._start_battle()
        data = self._test('battle_timer', self.world.uid, self.loc)
        expect = self._coerce(self.field.game.timer_view())
        self.assertEqual(expect, data['battle']['timer'])

    def test_unit_info(self):
        self.s._setup_default_defenders()
        unit = self.db['units'][2]
        data = self._test('unit', 2)
        expect = self._coerce(unit.api_view())
        self.assertEqual(expect, data['unit'])

    def test_stronghold_info(self):
        self._start_battle()
        data = self._test('stronghold', self.world.uid, self.loc)
        expect = self._coerce(self.f.stronghold.api_view())
        self.assertEqual(expect, data['stronghold'])
