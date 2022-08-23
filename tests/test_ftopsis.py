from unittest import TestCase
from unittest.mock import Mock, patch

from slr_worker_ranking.ftopsis import FuzzyTOPSIS


class TestFuzzyTOPSIS(TestCase):

    def setUp(self):
        self.rat_lf = {
            'very_good_rating': (9, 10, 10),
            'good_rating': (7, 9, 10),
            'medium_rating': (3, 5, 7),
            'poor_rating': (1, 3, 5),
            'very_poor_rating': (1, 1, 3)
        }
        self.crit_lf = {
            'high_weight': (0.7, 0.9, 1.0),
            'medium_high_weight': (0.5, 0.7, 0.9),
            'medium_weight': (0.3, 0.5, 0.7),
            'medium_low_weight': (0.1, 0.3, 0.5),
            'low_weight': (0.0, 0.1, 0.3),
        }


        self.dm_1 = {
            'decision_matrix': [
                [self.rat_lf['very_good_rating'], self.rat_lf['medium_rating'], self.rat_lf['poor_rating']],
                [self.rat_lf['medium_rating'], self.rat_lf['poor_rating'], self.rat_lf['medium_rating']]
            ],
            'criteria_weights': [ # weights for crit1, 2 and 3 as "high_weight", "medium_weight" the last two
                self.crit_lf['high_weight'], self.crit_lf['medium_weight'], self.crit_lf['medium_weight']
            ]
        }

        self.dm_2 = {
            'decision_matrix': [
                [self.rat_lf['medium_rating'], self.rat_lf['good_rating'], self.rat_lf['medium_rating']],
                [self.rat_lf['good_rating'], self.rat_lf['poor_rating'], self.rat_lf['very_good_rating']]
            ],
            'criteria_weights': [
                self.crit_lf['medium_weight'], self.crit_lf['medium_high_weight'], self.crit_lf['medium_high_weight']
            ]
        }
        self.criteria_benefit_indicator = [True, False, True] # crit1 and 3 are benefit, and crit 2 is cost
        self.ranker = FuzzyTOPSIS(criteria_benefit_indicator=self.criteria_benefit_indicator)
        self.ranker.add_decision_maker(**self.dm_1)
        self.ranker.add_decision_maker(**self.dm_2)

    def test_add_decision_maker(self):
        new_ranker = FuzzyTOPSIS(criteria_benefit_indicator=self.criteria_benefit_indicator)
        new_ranker.add_decision_maker(**self.dm_1)

        self.assertListEqual(new_ranker.decision_matrix_list, [self.dm_1['decision_matrix']])
        self.assertListEqual(new_ranker.criteria_weights_list, [self.dm_1['criteria_weights']])

        new_ranker.add_decision_maker(**self.dm_2)
        self.assertListEqual(new_ranker.decision_matrix_list, [self.dm_1['decision_matrix'], self.dm_2['decision_matrix']])
        self.assertListEqual(new_ranker.criteria_weights_list, [self.dm_1['criteria_weights'], self.dm_2['criteria_weights']])


    def test_defaut_alt_agg_fuzzy_rating_method(self):
        agg_alt_i_crit_j = self.ranker._defaut_alt_agg_fuzzy_rating_method(alt_i=0, crit_j=0)
        exp_agg_alt_i_crit_j = (3, 7.5, 10) # min(a) avg(b) max(c) of very_good_rating and medium_rating
        self.assertEqual(agg_alt_i_crit_j, exp_agg_alt_i_crit_j)

    def test_all_agg_ratings(self):
        agg_decision_matrix = self.ranker._all_agg_ratings()
        exp_alt1_ratings = [(3, 7.5, 10), (3, 7, 10), (1, 4, 7)]
        exp_alt2_ratings = [(3, 7, 10), (1, 3, 5), (3, 7.5, 10)]
        expected_ratings = [
            exp_alt1_ratings,
            exp_alt2_ratings
        ]
        self.assertEqual(len(agg_decision_matrix), 2)

        self.assertEqual(len(agg_decision_matrix[0]), 3)
        self.assertEqual(len(agg_decision_matrix[1]), 3)

        self.assertEqual(len(agg_decision_matrix[0][0]), 3)

        self.assertListEqual(agg_decision_matrix, expected_ratings)

    def test_defaut_crit_agg_fuzzy_weight_method(self):
        agg_crit_j_w = self.ranker._defaut_crit_agg_fuzzy_weight_method(crit_j=0)

        exp_agg_crit_j_w = (0.3, 0.7, 1.0) # min(a) avg(b) max(c) of high_weight and medium_weight
        self.assertEqual(agg_crit_j_w, exp_agg_crit_j_w)

    def test_all_agg_weights(self):
        agg_criteria_weights = self.ranker._all_agg_weights()
        exp_agg_crit_weights = [(0.3, 0.7, 1.0), (0.3, 0.6, 0.9), (0.3, 0.6, 0.9)]

        self.assertEqual(len(agg_criteria_weights), 3)
        self.assertEqual(len(agg_criteria_weights[0]), 3)
        self.assertEqual(len(agg_criteria_weights[1]), 3)
        self.assertEqual(len(agg_criteria_weights[2]), 3)

        self.assertListEqual(agg_criteria_weights, exp_agg_crit_weights)

    @patch('slr_worker_ranking.ftopsis.FuzzyTOPSIS._all_agg_ratings')
    @patch('slr_worker_ranking.ftopsis.FuzzyTOPSIS._all_agg_weights')
    def test_aggregated_ratings_and_weights_should_call_methods_and_set_vars(self, m_agg_w, m_agg_r):
        agg_r = 'mock agg alternatives'
        m_agg_r.return_value = agg_r
        agg_w = 'mock crit weights'
        m_agg_w.return_value = agg_w

        self.ranker._aggregated_ratings_and_weights()
        m_agg_r.assert_called_once()
        m_agg_w.assert_called_once()
        self.assertEqual(self.ranker.agg_decision_matrix, agg_r)
        self.assertEqual(self.ranker.agg_criteria_weights, agg_w)


    def test_get_min_left_or_max_right_for_criteria_for_benefit_criteria(self):
        self.ranker.agg_decision_matrix = [
            [(3, 7.5, 10), (3, 7, 10), (1, 4, 7)], # alt 1
            [(3, 7, 10), (1, 3, 5), (3, 7.5, 10)] # alt 2
        ]
        minl_or_maxr_criteria = self.ranker._get_min_left_or_max_right_for_criteria(crit_j=0)
        exp_value = 10
        self.assertEqual(minl_or_maxr_criteria, exp_value)

        minl_or_maxr_criteria = self.ranker._get_min_left_or_max_right_for_criteria(crit_j=2)
        exp_value = 10
        self.assertEqual(minl_or_maxr_criteria, exp_value)

    def test_get_min_left_or_max_right_for_criteria_for_cost_criteria(self):
        self.ranker.agg_decision_matrix = [
            [(3, 7.5, 10), (3, 7, 10), (1, 4, 7)], # alt 1
            [(3, 7, 10), (1, 3, 5), (3, 7.5, 10)] # alt 2
        ]
        minl_or_maxr_criteria = self.ranker._get_min_left_or_max_right_for_criteria(crit_j=1)
        exp_value = 1
        self.assertEqual(minl_or_maxr_criteria, exp_value)

    def test_default_normalize_alternative_method_for_benefit_criteria(self):
        self.ranker.agg_decision_matrix = [
            [(3, 7.5, 10), (3, 7, 10), (1, 4, 7)], # alt 1
            [(3, 7, 10), (1, 3, 5), (3, 7.5, 10)] # alt 2
        ]
        norm_alt_i_crit_j = self.ranker._default_normalize_alternative_method(alt_i=0, crit_j=0, minl_or_maxr_criteria=10)

        exp_norm_alt_i_crit_j = (0.3, 0.75, 1.0)
        self.assertEqual(norm_alt_i_crit_j, exp_norm_alt_i_crit_j)

    def test_default_normalize_alternative_method_for_cost_criteria(self):
        self.ranker.agg_decision_matrix = [
            [(3, 7.5, 10), (3, 7, 10), (1, 4, 7)], # alt 1
            [(3, 7, 10), (1, 3, 5), (3, 7.5, 10)] # alt 2
        ]
        norm_alt_i_crit_j = self.ranker._default_normalize_alternative_method(alt_i=0, crit_j=1, minl_or_maxr_criteria=1)

        exp_norm_alt_i_crit_j = (1/10, 1/7, 1/3)
        for v in range(len(exp_norm_alt_i_crit_j)):
            self.assertAlmostEqual(norm_alt_i_crit_j[v], exp_norm_alt_i_crit_j[v], places=2)

    def test_normalized_decision_matrix(self):
        self.ranker.agg_decision_matrix = [
            [(3, 7.5, 10), (3, 7, 10), (1, 4, 7)], # alt 1
            [(3, 7, 10), (1, 3, 5), (3, 7.5, 10)] # alt 2
        ]
        self.ranker._normalized_decision_matrix()
        exp_norm_decision_matrix = [
            [(0.3, 0.75, 1.0), (1/10, 1/7, 1/3), (0.1, 0.4, 0.7)], # alt1
            [(0.3, 0.7, 1.0), (1/5, 1/3, 1.0), (0.3, 0.75, 1)], # alt2
        ]
        self.assertEqual(self.ranker.norm_decision_matrix, exp_norm_decision_matrix)

    def test_weighted_normalized_decision_matrix(self):
        self.ranker.agg_criteria_weights = [(0.3, 0.7, 1.0), (0.3, 0.6, 0.9), (0.3, 0.6, 0.9)]
        self.ranker.norm_decision_matrix = [
            [(0.3, 0.75, 1.0), (0.1, 0.142, 1/3), (0.1, 0.4, 0.7)], # alt1
            [(0.3, 0.7, 1.0), (1/5, 1/3, 1.0), (0.3, 0.75, 1)], # alt2
        ]
        self.ranker._weighted_normalized_decision_matrix()
        exp_weighted_norm_decision_matrix = [
            [(0.3 * 0.3, 0.75 * 0.7, 1.0 * 1.0), (0.03, 0.142 * 0.6, 1/3 * 0.9), (0.1 * 0.3, 0.4 * 0.6, 0.7 * 0.9)], # alt1
            [(0.3 * 0.3, 0.7 * 0.7, 1.0 * 1.0), (1/5 * 0.3, 1/3 * 0.6, 1.0 * 0.9), (0.3 * 0.3, 0.75 * 0.6, 1.0 * 0.9)], # alt2
        ]
        for alt_i in range(self.ranker.num_alternatives):
            for crit_j in range(self.ranker.num_criteria):
                for triple_i in range(3):
                    self.assertAlmostEqual(
                        self.ranker.weighted_norm_decision_matrix[alt_i][crit_j][triple_i],
                        exp_weighted_norm_decision_matrix[alt_i][crit_j][triple_i],
                        places=3
                    )