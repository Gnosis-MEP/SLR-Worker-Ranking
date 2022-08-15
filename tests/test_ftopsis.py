from unittest import TestCase
from unittest.mock import Mock, patch

from slr_worker_ranking.ftopsis import FuzzyTOPSIS


class TestFuzzyTOPSIS(TestCase):
    
    def setUp(self):
        self.ranker = FuzzyTOPSIS(alt=[], k_benefit_crit=[], k_cost_crit=[])

    def test_all_agg_ratings(self):
        very_good_rating = (9, 10, 10)
        good_rating = (7, 9, 10)
        medium_rating = (3, 5, 7)
        poor_rating = (1, 3, 5)
        very_poor_rating = (1, 1, 3)

        criteria = ['c1', 'c2', 'c3']
        decision_makers = ['k1', 'k2', 'k3']
        alt1 = [
            [ very_good_rating, medium_rating, good_rating] 
            for c in criteria
        ]

        alt2 = [
            [ medium_rating, medium_rating, very_poor_rating] 
            for c in criteria
        ]

        self.ranker.alternatives = [
            alt1, 
            alt2
        ]
        all_agg_ratings = self.ranker._all_agg_ratings()


        exp_alt1_ratings = [(3, 8.0, 10), (3, 8.0, 10), (3, 8.0, 10)]
        exp_alt2_ratings = [(1, 3.666, 7), (1, 3.666, 7), (1, 3.666, 7)]
        expected_ratings = [
            exp_alt1_ratings,
            exp_alt2_ratings
        ]
        self.assertEqual(len(all_agg_ratings), 2)

        self.assertEqual(len(all_agg_ratings[0]), 3)
        self.assertEqual(len(all_agg_ratings[1]), 3)

        self.assertEqual(len(all_agg_ratings[0][0]), 3)

        
        for j in range(len(exp_alt1_ratings)):
            alt_1_ratings = all_agg_ratings[0]
            rating = alt_1_ratings[j]
            exp_rating = exp_alt1_ratings[j]
            for triple_val_index in range(3):
                self.assertAlmostEqual(exp_rating[triple_val_index], rating[triple_val_index], places=2)

        for j in range(len(exp_alt2_ratings)):
            alt_2_ratings = all_agg_ratings[1]
            rating = alt_2_ratings[j]
            exp_rating = exp_alt2_ratings[j]
            for triple_val_index in range(3):
                self.assertAlmostEqual(exp_rating[triple_val_index], rating[triple_val_index], places=2)



    def test_all_agg_weights(self):
        high_weight = (0.7, 0.9, 1.0)
        medium_high_weight = (0.5, 0.7, 0.9)
        medium_weight = (0.3, 0.5, 0.7)
        medium_low_weight = (0.1, 0.3, 0.5)
        low_weight = (0.0, 0.1, 0.3)


        criteria = ['c1', 'c2', 'c3']
        decision_makers = ['k1', 'k2', 'k3']
        self.ranker.benefit_criteria = [
            [high_weight, medium_high_weight, high_weight], # (0.5, 0.833, 1.0)
            [medium_weight, medium_low_weight, low_weight]  # (0.0, 0.3, 0.7)
        ]
        self.ranker.cost_criteria = [
            [low_weight, medium_weight, medium_weight], # (0.0, 0.366, 0.7)
            [low_weight, low_weight, low_weight] # (0.0, 0.1, 0.3)
        ]


        agg_benefit_crit, agg_cost_crit = self.ranker._all_agg_weights()


        exp_agg_benefit_crit = [(0.5, 0.833, 1.0), (0.0, 0.3, 0.7)]
        exp_agg_cost_crit = [(0.0, 0.366, 0.7), (0.0, 0.1, 0.3)]

        self.assertEqual(len(agg_benefit_crit), 2)
        self.assertEqual(len(agg_cost_crit), 2)

        self.assertEqual(len(agg_benefit_crit[0]), 3)
        self.assertEqual(len(exp_agg_cost_crit[0]), 3)


        
        for j in range(len(exp_agg_benefit_crit)):
            crit_w = agg_benefit_crit[j]
            exp_w = exp_agg_benefit_crit[j]
            for triple_val_index in range(3):
                self.assertAlmostEqual(exp_w[triple_val_index], crit_w[triple_val_index], places=2)

        for j in range(len(exp_agg_cost_crit)):
            crit_w = agg_cost_crit[j]
            exp_w = exp_agg_cost_crit[j]
            for triple_val_index in range(3):
                self.assertAlmostEqual(exp_w[triple_val_index], crit_w[triple_val_index], places=2)

    @patch('slr_worker_ranking.ftopsis.FuzzyTOPSIS._all_agg_ratings')
    @patch('slr_worker_ranking.ftopsis.FuzzyTOPSIS._all_agg_weights')
    def test_aggregated_ratings_and_weights_should_call_methods_and_set_vars(self, m_agg_w, m_agg_r):
        agg_r = 'agg alternatives'
        m_agg_r.return_value = agg_r
        agg_w = ['Benefit crit weights', 'cost crit weights']
        m_agg_w.return_value = agg_w

        self.ranker._aggregated_ratings_and_weights()
        m_agg_r.assert_called_once()
        m_agg_w.assert_called_once()
        self.assertEqual(self.ranker.agg_alternatives, agg_r)
        self.assertEqual(self.ranker.agg_benefit_criteria, agg_w[0])
        self.assertEqual(self.ranker.agg_cost_criteria, agg_w[1])