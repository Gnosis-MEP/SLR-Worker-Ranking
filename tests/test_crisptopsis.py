from unittest import TestCase
from unittest.mock import Mock, patch

from slr_worker_ranking.mcdm.crisptopsis import CrispTOPSIS


class TestCrispTOPSIS(TestCase):

    def setUp(self):
        self.rat_lf = {
            'very_good_rating': 10,
            'good_rating': 8,
            'medium_rating': 5,
            'poor_rating': 3,
            'very_poor_rating': 1
        }
        self.crit_lf = {
            'high_weight': 1.0,
            'medium_high_weight': 0.7,
            'medium_weight': 0.5,
            'medium_low_weight': 0.3,
            'low_weight': 0.1,
        }

        self.dm_1 = {
            'decision_matrix': [
                [self.rat_lf['medium_rating'], self.rat_lf['poor_rating'], self.rat_lf['medium_rating']],
                [self.rat_lf['very_good_rating'], self.rat_lf['medium_rating'], self.rat_lf['poor_rating']],
            ],
            'criteria_weights': [ # weights for crit1, 2 and 3 as "high_weight", "medium_weight" the last two
                self.crit_lf['high_weight'], self.crit_lf['medium_weight'], self.crit_lf['medium_weight']
            ]
        }

        self.criteria_benefit_indicator = [True, False, True] # crit1 and 3 are benefit, and crit 2 is cost
        self.decision_matrix_list = [self.dm_1['decision_matrix']]
        self.criteria_weights_list = [self.dm_1['criteria_weights']]
        self.ranker = CrispTOPSIS(
            criteria_benefit_indicator=self.criteria_benefit_indicator
        )

    def test_evalute_end_to_end(self):
        self.ranker.add_decision_maker(**self.dm_1)
        ret = self.ranker.evaluate()
        expected_rank_index = [1, 0]
        self.assertListEqual(ret, expected_rank_index)

        scores = self.ranker.get_alternatives_ranking_scores()
        expected_ccs = [0.3516287, 0.6483713]
        self.assertAlmostEqual(scores[0], expected_ccs[0], places=3)
        self.assertAlmostEqual(scores[1], expected_ccs[1], places=3)

    def test_logically_sound_example_cost_criteria(self):
        criteria_rank = {
            'high_importance': 0.9,
            'medium_high_importance': 0.7,
            'medium_importance': 0.5,
            'medium_low_importance': 0.3,
            'low_importance': 0.1,
        }
        alternative_rating = {
            'high_rating': 9,
            'medium_high_rating': 7,
            'medium_rating': 5,
            'medium_low_rating': 3,
            'low_rating': 1,
        }
        alternative_d_rating = {
            'high_rating': 0.9,
            'medium_high_rating': 0.7,
            'medium_rating': 0.5,
            'medium_low_rating': 0.3,
            'low_rating': 0.1,
        }
        alternative_c_rating = {
            'high_rating': 90,
            'medium_high_rating': 70,
            'medium_rating': 50,
            'medium_low_rating': 30,
            'low_rating': 10,
        }


        dm_single = {
            'decision_matrix': [
                [alternative_d_rating['medium_rating'], alternative_c_rating['medium_rating'], alternative_rating['low_rating']],
                [alternative_d_rating['medium_rating'], alternative_c_rating['medium_rating'], alternative_rating['high_rating']],
                [alternative_d_rating['high_rating'], alternative_c_rating['low_rating'], alternative_rating['medium_rating']],
            ],
            'criteria_weights': [
                criteria_rank['medium_importance'], criteria_rank['low_importance'], criteria_rank['high_importance']
            ]
        }

        criteria_benefit_indicator = [True, True, False] # crit1 and 2 are benefit, and crit 3 is cost
        decision_matrix_list = [dm_single['decision_matrix']]
        criteria_weights_list = [dm_single['criteria_weights']]
        self.ranker = CrispTOPSIS(
            criteria_benefit_indicator=criteria_benefit_indicator
        )

        self.ranker.add_decision_maker(**dm_single)
        ret = self.ranker.evaluate()
        expected_rank_index = [1, 0]

        self.assertEqual(ret[0], 0)
        self.assertListEqual(ret, [0, 2, 1])
