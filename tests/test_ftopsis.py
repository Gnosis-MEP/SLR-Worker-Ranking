from unittest import TestCase
from unittest.mock import patch

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
