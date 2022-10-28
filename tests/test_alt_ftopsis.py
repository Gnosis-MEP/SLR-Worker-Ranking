from unittest import TestCase
from unittest.mock import Mock, patch

from slr_worker_ranking.mcdm.ftopsis import AltFuzzyTOPSIS


class TestAltuzzyTOPSIS(TestCase):

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
        self.ranker = AltFuzzyTOPSIS(
            criteria_benefit_indicator=self.criteria_benefit_indicator,
            decision_matrix_list=self.decision_matrix_list,
            criteria_weights_list=self.criteria_weights_list
        )


    def test_defaut_alt_agg_fuzzy_rating_method(self):
        agg_alt_i_crit_j = self.ranker._defaut_alt_agg_fuzzy_rating_method(alt_i=0, crit_j=0)
        exp_agg_alt_i_crit_j = [3, 7.5, 10] # min(a) avg(b) max(c) of very_good_rating and medium_rating
        self.assertEqual(agg_alt_i_crit_j, exp_agg_alt_i_crit_j)


    def test_calculate_FPIS_FNIS(self):
        self.ranker.weighted_norm_decision_matrix = [
            [(0.09, 0.524, 1.0), (0.03, 0.085, 0.3), (0.03, 0.24, 0.63)],
            [(0.09, 0.489, 1.0), (0.06, 0.199, 0.9), (0.09, 0.449, 0.9)]
        ]

        self.ranker._calculate_FPIS_FNIS()
        exp_FPIS_indexes = [0, 1, 1]
        exp_FNIS_indexes = [1, 0, 0]

        self.assertListEqual(self.ranker.FPIS_indexes, exp_FPIS_indexes)
        self.assertListEqual(self.ranker.FNIS_indexes, exp_FNIS_indexes)

    def test_fuzzy_number_distance_calculation(self):
        dist = self.ranker._fuzzy_number_distance_calculation((1.0,2.0,3.0), (6.0, 5.0, 4.0))
        exp_dist = 3.415650255
        self.assertAlmostEqual(dist, exp_dist, places=2)


    def test_calculate_distance_from_ideal_solutions(self):
        self.ranker.weighted_norm_decision_matrix = [
            [(0.09, 0.524, 1.0), (0.03, 0.085, 0.3), (0.03, 0.24, 0.63)],
            [(0.09, 0.489, 1.0), (0.06, 0.199, 0.9), (0.09, 0.449, 0.9)]
        ]

        self.ranker.FPIS_indexes = [0, 1, 1]
        self.ranker.FNIS_indexes = [1, 0, 0]
        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=0, crit_j=0, is_positive=True)
        exp_dist = 0
        self.assertEqual(dist, exp_dist)
        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=1, crit_j=0, is_positive=True)
        exp_dist = self.ranker._fuzzy_number_distance_calculation((0.09, 0.489, 1.0), (0.09, 0.524, 1.0))
        self.assertAlmostEqual(dist, exp_dist)

        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=0, crit_j=0, is_positive=False)
        exp_dist = self.ranker._fuzzy_number_distance_calculation((0.09, 0.524, 1.0), (0.09, 0.489, 1.0))
        self.assertAlmostEqual(dist, exp_dist)

        dist = self.ranker._calculate_distance_from_ideal_solutions(alt_i=1, crit_j=0, is_positive=False)
        exp_dist = 0
        self.assertEqual(dist, exp_dist)


    def test_distance_from_FPIS_FNIS(self):
        self.ranker.weighted_norm_decision_matrix = [
            [(0.09, 0.524, 1.0), (0.03, 0.085, 0.3), (0.03, 0.24, 0.63)],
            [(0.09, 0.489, 1.0), (0.06, 0.199, 0.9), (0.09, 0.449, 0.9)]
        ]

        self.ranker.FPIS_indexes = [0, 1, 1]
        self.ranker.FNIS_indexes = [1, 0, 0]

        self.ranker._distance_from_FPIS_FNIS()

        exp_fpis_distances_per_criterion = [
            [0, 0.353, 0.200],
            [0.020, 0, 0]
        ]
        exp_fpis_distances = [0.553, 0.02]
        exp_fnis_distances_per_criterion = [
            [0.0202, 0, 0],
            [0, 0.353, 0.200]
        ]
        exp_fnis_distances = [0.02, 0.553]


        self.assertAlmostEqual(self.ranker.fpis_distances[0], exp_fpis_distances[0], places=3)
        self.assertAlmostEqual(self.ranker.fpis_distances[1], exp_fpis_distances[1], places=3)

        self.assertAlmostEqual(self.ranker.fnis_distances[0], exp_fnis_distances[0], places=3)
        self.assertAlmostEqual(self.ranker.fnis_distances[1], exp_fnis_distances[1], places=3)