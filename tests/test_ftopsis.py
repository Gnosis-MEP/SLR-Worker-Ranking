from unittest import TestCase
from unittest.mock import Mock, patch

import numpy as np

from slr_worker_ranking.mcdm.ftopsis import FuzzyTOPSIS, AltFuzzyTOPSIS


class TestFuzzyTOPSIS(TestCase):
    """
    Testing general stuff with my own inputs
    """
    def setUp(self):
        # Sorin N˘ad˘aban et al. / Procedia Computer Science 91 ( 2016 ) 823 – 831 (Table 2. Linguistic terms for alternatives ratings)
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
        self.decision_matrix_list = [self.dm_1['decision_matrix'], self.dm_2['decision_matrix']]
        self.criteria_weights_list = [self.dm_1['criteria_weights'], self.dm_2['criteria_weights']]
        self.ranker = FuzzyTOPSIS(
            criteria_benefit_indicator=self.criteria_benefit_indicator,
            decision_matrix_list=self.decision_matrix_list,
            criteria_weights_list=self.criteria_weights_list
        )

    def test_add_decision_maker(self):
        new_ranker = FuzzyTOPSIS(criteria_benefit_indicator=self.criteria_benefit_indicator)
        new_ranker.add_decision_maker(**self.dm_1)

        self.assertListEqual(new_ranker.decision_matrix_list, [self.dm_1['decision_matrix']])
        self.assertListEqual(new_ranker.criteria_weights_list, [self.dm_1['criteria_weights']])

        new_ranker.add_decision_maker(**self.dm_2)
        self.assertListEqual(new_ranker.decision_matrix_list, [self.dm_1['decision_matrix'], self.dm_2['decision_matrix']])
        self.assertListEqual(new_ranker.criteria_weights_list, [self.dm_1['criteria_weights'], self.dm_2['criteria_weights']])


    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._all_agg_ratings')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._all_agg_weights')
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


    def test_calculate_FPIS_FNIS(self):
        self.ranker.weighted_norm_decision_matrix = [
            [(0.09, 0.524, 1.0), (0.03, 0.085, 0.3), (0.03, 0.24, 0.63)],
            [(0.09, 0.489, 1.0), (0.06, 0.199, 0.9), (0.09, 0.449, 0.9)]
        ]

        self.ranker._calculate_FPIS_FNIS()
        exp_FPIS_value = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        exp_FNIS_value = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        self.assertListEqual(self.ranker.FPIS_value, exp_FPIS_value)
        self.assertListEqual(self.ranker.FNIS_value, exp_FNIS_value)

    def test_fuzzy_number_distance_calculation(self):
        dist = self.ranker._fuzzy_number_distance_calculation((1.0,2.0,3.0), (6.0, 5.0, 4.0))
        exp_dist = 3.415650255
        self.assertAlmostEqual(dist, exp_dist, places=2)


    def test_calculate_distance_from_ideal_solutions(self):
        self.ranker.weighted_norm_decision_matrix = [
            [(0.09, 0.524, 1.0), (0.03, 0.085, 0.3), (0.03, 0.24, 0.63)],
            [(0.09, 0.489, 1.0), (0.06, 0.199, 0.9), (0.09, 0.449, 0.9)]
        ]
        self.ranker.FPIS_value = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        self.ranker.FNIS_value = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=0, crit_j=0, is_positive=True)
        exp_dist = 0.59
        self.assertAlmostEqual(dist, exp_dist, places=2)
        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=1, crit_j=0, is_positive=True)
        exp_dist = self.ranker._fuzzy_number_distance_calculation((0.09, 0.489, 1.0), (1, 1, 1))
        self.assertAlmostEqual(dist, exp_dist, places=2)

        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=0, crit_j=0, is_positive=False)
        exp_dist = self.ranker._fuzzy_number_distance_calculation((0.09, 0.524, 1.0), (0, 0, 0))
        self.assertAlmostEqual(dist, exp_dist, places=2)

        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=1, crit_j=0, is_positive=False)
        exp_dist = self.ranker._fuzzy_number_distance_calculation((0.09, 0.489, 1.0), (0, 0, 0))
        self.assertAlmostEqual(dist, exp_dist, places=2)

    def test_distance_from_FPIS_FNIS(self):
        self.ranker.weighted_norm_decision_matrix = [
            [(0.09, 0.524, 1.0), (0.03, 0.085, 0.3), (0.03, 0.24, 0.63)],
            [(0.09, 0.489, 1.0), (0.06, 0.199, 0.9), (0.09, 0.449, 0.9)]
        ]

        self.ranker.FPIS_value = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
        self.ranker.FNIS_value = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

        self.ranker._distance_from_FPIS_FNIS()

        exp_fpis_distances_per_criterion = [
            [0.5929238287222623, 0.8695065650509297, 0.7428324171709255],
            [0.6025559448438516, 0.7153556225169875, 0.616901126599717]
        ]

        exp_fpis_distances = [2.2052628109441175, 1.934812693960556]
        exp_fnis_distances_per_criterion = [
            [0.65, 0.18, 0.39],
            [0.64, 0.53, 0.58]
        ]
        exp_fnis_distances = [1.22, 1.76]

        np.testing.assert_almost_equal(self.ranker.fpis_distances, exp_fpis_distances, decimal=2)
        np.testing.assert_almost_equal(self.ranker.fnis_distances, exp_fnis_distances, decimal=2)


    def test_calculate_closeness_coefficients(self):
        self.ranker.fpis_distances = [0.553, 0.02]
        self.ranker.fnis_distances = [0.02, 0.553]
        self.ranker._calculate_closeness_coefficients()
        expected_ccs = [0.0349, 0.965]
        self.assertAlmostEqual(self.ranker.closeness_coefficients[0], expected_ccs[0], places=3)
        self.assertAlmostEqual(self.ranker.closeness_coefficients[1], expected_ccs[1], places=3)

    def test_rank_alternatives(self):
        self.ranker.closeness_coefficients = [0.035, 0.965]
        expected_rank_index = [1, 0]
        self.ranker._rank_alternatives()
        self.assertListEqual(self.ranker.ranking_indexes, expected_rank_index)

    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS.validate_inputs')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._aggregated_ratings_and_weights')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._normalized_decision_matrix')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._weighted_normalized_decision_matrix')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._calculate_FPIS_FNIS')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._distance_from_FPIS_FNIS')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._calculate_closeness_coefficients')
    @patch('slr_worker_ranking.mcdm.ftopsis.FuzzyTOPSIS._rank_alternatives')
    def test_evaluate_calls_all_steps_and_returns_ranking_indexes(self, m_8, m_7, m_6, m_5, m_4, m_3, m_2, m_1):
        self.ranker.ranking_indexes = 'mocked'
        ret = self.ranker.evaluate()
        m_1.assert_called_once()
        m_2.assert_called_once()
        m_3.assert_called_once()
        m_4.assert_called_once()
        m_5.assert_called_once()
        m_6.assert_called_once()
        m_7.assert_called_once()
        m_8.assert_called_once()
        self.assertEqual(ret, 'mocked')

    def test_evalute_end_to_end(self):
        ret = self.ranker.evaluate()
        expected_rank_index = [1, 0]
        self.assertListEqual(ret, expected_rank_index)
        expected_ccs = [0.352, 0.495]
        self.assertAlmostEqual(self.ranker.closeness_coefficients[0], expected_ccs[0], places=3)
        self.assertAlmostEqual(self.ranker.closeness_coefficients[1], expected_ccs[1], places=3)


class TestFuzzyTOPSISWithChenInputs(TestCase):

    def setUp(self):
        self.crit_lf = {
            'VH': (0.9, 1.0, 1.0),
            'H': (0.7, 0.9, 1.0),
            'MH': (0.5, 0.7, 0.9),
            'M': (0.3, 0.5, 0.7),
            'ML': (0.1, 0.3, 0.5),
            'L': (0, 0.1, 0.3),
            'VL': (0.0, 0.0, 0.1),
        }

        self.rat_lf = {
            'VG': (9, 10, 10),
            'G': (7, 9, 10),
            'MG': (5, 7, 9),
            'F': (3, 5, 7),
            'MP': (1, 3, 5),
            'P': (0, 1, 3),
            'VP': (0, 0, 1)
        }


        self.dm_1 = {
            'decision_matrix': [
                [self.rat_lf['MG'], self.rat_lf['G'], self.rat_lf['F'], self.rat_lf['VG'], self.rat_lf['F']],
                [self.rat_lf['G'], self.rat_lf['VG'], self.rat_lf['VG'], self.rat_lf['VG'], self.rat_lf['VG']],
                [self.rat_lf['VG'], self.rat_lf['MG'], self.rat_lf['G'], self.rat_lf['G'], self.rat_lf['G']],
            ],
            'criteria_weights': [
                self.crit_lf['H'], self.crit_lf['VH'], self.crit_lf['VH'], self.crit_lf['VH'], self.crit_lf['M']
            ]
        }

        self.dm_2 = {
            'decision_matrix': [
                [self.rat_lf['G'], self.rat_lf['MG'], self.rat_lf['G'], self.rat_lf['G'], self.rat_lf['F']],
                [self.rat_lf['G'], self.rat_lf['VG'], self.rat_lf['VG'], self.rat_lf['VG'], self.rat_lf['MG']],
                [self.rat_lf['G'], self.rat_lf['G'], self.rat_lf['MG'], self.rat_lf['VG'], self.rat_lf['G']],
            ],
            'criteria_weights': [
                self.crit_lf['VH'], self.crit_lf['VH'], self.crit_lf['H'], self.crit_lf['VH'], self.crit_lf['MH']
            ]
        }

        self.dm_3 = {
            'decision_matrix': [
                [self.rat_lf['MG'], self.rat_lf['F'], self.rat_lf['G'], self.rat_lf['VG'], self.rat_lf['F']],
                [self.rat_lf['MG'], self.rat_lf['VG'], self.rat_lf['G'], self.rat_lf['VG'], self.rat_lf['G']],
                [self.rat_lf['F'], self.rat_lf['VG'], self.rat_lf['VG'], self.rat_lf['MG'], self.rat_lf['MG']],
            ],
            'criteria_weights': [
                self.crit_lf['MH'], self.crit_lf['VH'], self.crit_lf['H'], self.crit_lf['VH'], self.crit_lf['MH']
            ]
        }

        self.criteria_benefit_indicator = [True, True, True, True, True]
        self.decision_matrix_list = [self.dm_1['decision_matrix'], self.dm_2['decision_matrix'], self.dm_3['decision_matrix']]
        self.criteria_weights_list = [self.dm_1['criteria_weights'], self.dm_2['criteria_weights'], self.dm_3['criteria_weights']]
        self.ranker = FuzzyTOPSIS(
            criteria_benefit_indicator=self.criteria_benefit_indicator,
            decision_matrix_list=self.decision_matrix_list,
            criteria_weights_list=self.criteria_weights_list
        )

    def test_defaut_alt_agg_fuzzy_rating_method(self):
        agg_alt_i_crit_j = self.ranker._defaut_alt_agg_fuzzy_rating_method(alt_i=0, crit_j=0)
        exp_agg_alt_i_crit_j = [5.67, 7.67, 9.33]
        np.testing.assert_almost_equal(agg_alt_i_crit_j, exp_agg_alt_i_crit_j, decimal=2)

    def test_all_agg_ratings(self):
        agg_decision_matrix = self.ranker._all_agg_ratings()
        exp_alt1_ratings = [[5.67, 7.67, 9.33], [5, 7, 8.67], [5.67, 7.67, 9], [8.33, 9.67, 10], [3, 5, 7]]
        np.testing.assert_array_almost_equal(agg_decision_matrix[0], exp_alt1_ratings, decimal=2)

        exp_alt2_ratings = [[6.33, 8.33, 9.67], [9.0, 10.0, 10.0], [8.33, 9.67, 10.0], [9.0, 10.0, 10.0], [7.0, 8.67, 9.67]]
        exp_alt3_ratings = [[6.33, 8.0, 9.0], [7.0, 8.67, 9.67], [7.0, 8.67, 9.67], [7.0, 8.67, 9.67], [6.33, 8.33, 9.67]]
        expected_ratings = [
            exp_alt1_ratings,
            exp_alt2_ratings,
            exp_alt3_ratings
        ]
        self.assertEqual(len(agg_decision_matrix), 3)

        self.assertEqual(len(agg_decision_matrix[0]), 5)
        self.assertEqual(len(agg_decision_matrix[1]), 5)
        self.assertEqual(len(agg_decision_matrix[2]), 5)

        self.assertEqual(len(agg_decision_matrix[0][0]), 3)

        np.testing.assert_array_almost_equal(agg_decision_matrix, expected_ratings, decimal=2)

    def test_defaut_crit_agg_fuzzy_weight_method(self):
        agg_weight_crit_j = self.ranker._defaut_crit_agg_fuzzy_weight_method(crit_j=0)
        exp_agg_weight_crit_j = [0.7, 0.87, 0.97]
        np.testing.assert_almost_equal(agg_weight_crit_j, exp_agg_weight_crit_j, decimal=2)

    def test_all_agg_weights(self):
        agg_criteria_weights = self.ranker._all_agg_weights()
        exp_agg_crit_weights = [[0.7, 0.87, 0.97], [0.9, 1.0, 1.0], [0.77, 0.93, 1], [0.9, 1.0, 1.0], [0.43, 0.63, 0.83]]

        self.assertEqual(len(agg_criteria_weights), 5)
        self.assertEqual(len(agg_criteria_weights[0]), 3)
        np.testing.assert_almost_equal(agg_criteria_weights, exp_agg_crit_weights, decimal=2)


    def test_evalute_end_to_end(self):
        ret = self.ranker.evaluate()
        expected_rank_index = [1, 2, 0]
        self.assertListEqual(ret, expected_rank_index)

        # deviation from reported values in Chen's original paper  (0.62, 0.77, 0.71)
        # the rounding of numbers and a wrong value on Table 5 (aggregated attributes) for A1, C2
        # could be the culprit for this disdrepancy
        expected_ccs = [0.64, 0.77, 0.70]
        self.assertAlmostEqual(self.ranker.closeness_coefficients[1], expected_ccs[1], places=2)
        self.assertAlmostEqual(self.ranker.closeness_coefficients[2], expected_ccs[2], places=2)
        self.assertAlmostEqual(self.ranker.closeness_coefficients[0], expected_ccs[0], places=2)

