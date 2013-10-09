from mock import patch
from unittest import TestCase
from equanimity.const import E, F, I, W
from equanimity.stone import Composition
from equanimity.transmuter import Transmuter


class TransmuterTest(TestCase):

    def setUp(self):
        super(TransmuterTest, self).setUp()
        self.setup_transmuter(Composition.create(1, 2, 2, 2),
                              Composition.create(2, 1, 0, 0))

    def setup_transmuter(self, silo, need):
        self.s = silo
        self.n = need
        self.t = Transmuter(self.s, self.n)

    def test_create(self):
        self.assertEqual(self.t.silo, dict(self.s))
        self.assertEqual(self.t.need, dict(self.n))
        self.assertIs(self.t.solution, None)
        self.assertFalse(self.t.failed)

    def test_filter_zeroes(self):
        d = dict(a=0, b=1, c=0, d=7)
        self.assertEqual(self.t._filter_zeroes(d), dict(b=1, d=7))

    def test_prepare_comps(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        self.assertEqual(a, {F: 1, I: 2, W: 2})
        self.assertEqual(b, {E: 1})

    @patch.object(Composition, 'sanity_check')
    def test_prepare_comps_invalid(self, mock_sanity_check):
        need = Composition(-1)
        self.assertRaises(ValueError, self.t._prepare_comps, self.t.silo, need)

    def test_generate_variables(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        v, s = self.t._generate_variables(a, b)
        expect_v = ['needE', 'siloF', 'siloI', 'siloW']
        expect_v += ['siloFE', 'siloIE', 'siloWE']
        expect_s = {F[0]: ['siloFE'], I[0]: ['siloIE'], W[0]: ['siloWE']}
        self.assertEqual(sorted(v), sorted(expect_v))
        self.assertEqual(sorted(s), sorted(expect_s))

    def test_generate_constraints(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        v, s = self.t._generate_variables(a, b)
        c = self.t._generate_constraints(a, b, v, s)
        expect_c = ['siloF == 1', 'siloI == 2', 'siloW == 2',
                    'siloF >= siloFE', 'siloI >= siloIE', 'siloW >= siloWE',
                    'needE == 1',
                    'needE == (siloFE/2) + (siloIE/2) + (siloWE/4)']
        c = [x.formula for x in c]
        self.assertEqual(sorted(c), sorted(expect_c))

    def test_generate_constraints_completeness(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        # put a contrived value in, to get siloEE variables in
        # this should not happen since we prefilter, but _generate_constraints
        # should not be implemented to correctness and not assumption
        a[E] = 1
        v, s = self.t._generate_variables(a, b)
        c = self.t._generate_constraints(a, b, v, s)
        expect_c = ['siloF == 1', 'siloI == 2', 'siloW == 2', 'siloE == 1',
                    'siloF >= siloFE', 'siloI >= siloIE', 'siloW >= siloWE',
                    'siloE >= siloEE', 'needE == 1',
                    'needE == siloEE + (siloFE/2) + (siloIE/2) + (siloWE/4)']
        c = [x.formula for x in c]
        self.assertEqual(sorted(c), sorted(expect_c))

    def test_generate_domains(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        v, _ = self.t._generate_variables(a, b)
        d = self.t._generate_domains(a, b, v)
        expect_d = dict(siloF=[0, 1], siloI=[0, 1, 2], siloW=[0, 1, 2],
                        siloFE=[0, 1], siloIE=[0, 1, 2], siloWE=[0, 1, 2],
                        needE=[1])
        d = {k: v.getValues() for k, v in d.iteritems()}
        self.assertEqual(d, expect_d)

    def test_fail(self):
        self.assertRaises(ValueError, self.t._fail)
        self.assertTrue(self.t.failed)

    def test_solve(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        v, s = self.t._generate_variables(a, b)
        d = self.t._generate_domains(a, b, v)
        c = self.t._generate_constraints(a, b, v, s)
        sol = self.t._solve(v, d, c)
        expect_sol = dict(siloW=2, siloI=2, needE=1, siloF=1,
                          siloFE=0, siloIE=2, siloWE=0)
        self.assertEqual(sol, expect_sol)

    def test_compute_cost_failed(self):
        self.assertRaises(ValueError, self.t._compute_cost, None)
        self.assertTrue(self.t.failed)

    def test_compute_cost(self):
        a, b = self.t._prepare_comps(self.t.silo, self.t.need)
        v, s = self.t._generate_variables(a, b)
        d = self.t._generate_domains(a, b, v)
        c = self.t._generate_constraints(a, b, v, s)
        sol = self.t._solve(v, d, c)
        cost = self.t._compute_cost(sol)
        self.assertEqual(cost, Composition.create(0, 0, 2, 0))

    def test_get_cost_already_failed(self):
        self.t.failed = True
        self.assertRaises(ValueError, self.t.get_cost)

    def test_get_cost_already_solved(self):
        self.t.solution = dict(Earth=7, Fire=0, Ice=0, Wind=0)
        self.assertEqual(self.t.get_cost().comp, Composition.create(earth=7))

    def test_get_cost(self):
        cost = self.t.get_cost()
        self.assertEqual(cost.comp, Composition.create(0, 0, 2, 0))
        self.assertEqual(self.t.solution, dict(cost.comp))
        self.assertFalse(self.t.failed)

    def test_get_cost_simple_solution(self):
        self.setup_transmuter(Composition(10), Composition(8))
        cost = self.t.get_cost()
        self.assertEqual(cost.comp, Composition(8))
        self.assertEqual(self.t.solution, dict(cost.comp))
        self.assertFalse(self.t.failed)

    def test_get_cost_obviously_no_solution(self):
        self.setup_transmuter(Composition(8), Composition(10))
        self.assertFalse(self.t.failed)
        self.assertRaises(ValueError, self.t.get_cost)
        self.assertTrue(self.t.failed)
        self.assertIs(self.t.solution, None)
