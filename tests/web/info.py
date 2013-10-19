from voluptuous import Schema, Any
from battle import BattleTestBase


class InfoTest(BattleTestBase):

    service_name = 'info'

    def setUp(self):
        super(InfoTest, self).setUp()
        self._setup_schemas()

    def _setup_schemas(self):
        self.clock_schema = Schema(dict(clock=dict()))  # TODO
        self._field_schema = dict(
            owner=int, element=unicode, coordinate=[int, int], in_battle=bool
        )
        self.field_schema = Schema(dict(field=self._field_schema))
        self.world_schema = Schema(dict(
            world=dict(visible_fields=[self._field_schema])
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
            weapon=Any(None, dict), weapon_bonus=dict, equip_limit=dict,
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
        self._test('world')

    def test_field_info(self):
        data = self._test('field', self.loc)
        expect = self._coerce(self.field.api_view())
        self.assertEqual(expect, data['field'])

    def test_clock_info(self):
        self._test('clock')

    def test_battle_info(self):
        self.maxDiff = None
        self._start_battle()
        data = self._test('battle', self.loc)
        expect = self._coerce(self.field.game.api_view())
        self.assertEqual(expect, data['battle'])

    def test_battle_timer_info(self):
        self._start_battle()
        data = self._test('battle_timer', self.loc)
        expect = self._coerce(self.field.game.timer_view())
        self.assertEqual(expect, data['battle']['timer'])

    def test_unit_info(self):
        unit = self.db['units'][2]
        data = self._test('unit', 2)
        expect = self._coerce(unit.api_view())
        self.assertEqual(expect, data['unit'])
