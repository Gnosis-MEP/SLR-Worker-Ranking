
class FuzzyTOPSIS(object):
    """
    Class for running the Fuzzy TOPSIS ranking.

    Parameters
    ----------

    """


    def __init__(self, alt, k_benefit_crit, k_cost_crit):
        self.validate_inputs(alt, k_benefit_crit, k_cost_crit)

        self.alternatives = alt
        self.benefit_criteria = k_benefit_crit
        self.cost_criteria = k_cost_crit
        self.agg_alt_fuzzy_method = self._defaut_alt_agg_fuzzy_rating_method


    def validate_inputs(self, alt, k_benefit_crit, k_cost_crit):
        assert len(k_benefit_crit) == len(k_cost_crit), "Inconsistent decision makers criteria vectors lenght."
        assert len(k_benefit_crit) == len(alt), "Inconsistent decision makers alternatives vectors lenght."
    
    def evaluate(self):
        # self._assign_ratings_and_weights()
        self._aggregated_ratings_and_weights()
        self._normalized_decision_matrix()
        self._weighted_normalized_decision_matrix()
        self._calculate_FPIS_FNIS()
        self._distance_from_FPIS_FNIS()
        self._closeness_coefficient()
        alternatives_ranking = self._rank_alternatives()
        return alternatives_ranking


    # def _assign_ratings(self):
    #     """
    #     First step in fuzzy TOPSIS, where ratings are assigned to all criteria and alternatives
    #     """

    #     for i in len(self.alternatives):
    #         i_alt = self.alternatives[i]
    #         for j in range(len(i_alt)):
    #             i_j_crit = i_alt[j]
    #             for k in range(len(i_j_crit)):
    #                 # (9, 10, 10) -> Very Good
    #                 i_j_k_fuzzy_rating = i_j_crit[k]
    #                 pass

    #     for k in range(len(self.alternatives)):
    #         k_alternatives = self.alternatives[k]
    #         for i in range(len(k_alternatives)):
    #             i_alt = k_alternatives[i]
    #             for j in range(len(i_alt)):
    #                 k_i_j_crit = i_alt[j]
    #             i_alt = [cj_k]
    #             k_i_alt_fuzzy_ratings  


    def _defaut_alt_agg_fuzzy_rating_method(self, crit_alt):
        left_value, middle_value, right_value = crit_alt[0]

        total_decision_makers = len(crit_alt)
        # for each decision maker K rating specified for this criteria alternative (initialising with first K)
        for crit_alt_k in crit_alt[1:]:
            left_value = min(left_value, crit_alt_k[0])
            middle_value += crit_alt_k[1]
            right_value = max(right_value, crit_alt_k[2])
        middle_value = middle_value / total_decision_makers

        return (left_value, middle_value, right_value)


    def _all_agg_ratings(self):
        """
            Function used to aggregate the fuzzy ratings for the alternativas
        """
        agg_alt_ratings = []
        for i in range(len(self.alternatives)):
            agg_alt_i_ratings = []
            i_alt_criterias = self.alternatives[i]
            for j in range(len(i_alt_criterias)):
                i_j_crit_alt = i_alt_criterias[j]
                agg_rating = self.agg_alt_fuzzy_method(i_j_crit_alt)
                agg_alt_i_ratings.append(agg_rating)
            agg_alt_ratings.append(agg_alt_i_ratings)
        return agg_alt_ratings

    def _aggregated_ratings_and_weights(self):
        """
        Second step in fuzzy TOPSIS, where the aggregated fuzzy ratings and weights are calculated 
        for the criteria and alternatives, respectivelly.
        """

    def _normalized_decision_matrix(self):
        """
        Third step in fuzzy TOPSIS, in which the normalized fuzzy decision matrix is calculated.
        """

    def _weighted_normalized_decision_matrix(self):
        """
        Fourth step in fuzzy TOPSIS, in which the weighted normalized fuzzy decision matrix is calculated.
        """

    def _calculate_FPIS_FNIS(self):
        """
        Fifith step in fuzzy TOPSIS, in which the 
        Fuzzy Positive Ideal Solution (FPIS) and Fuzzy Negative Ideal Solution (FNIS) are calculated.
        """


    def _distance_from_FPIS_FNIS(self):
        """
        Sixth step in fuzzy TOPSIS, where the distances from each alternative to the 
        Fuzzy Positive Ideal Solution (FPIS) and Fuzzy Negative Ideal Solution (FNIS) are calculated.
        """

    def _closeness_coefficient(self):
        """
        Seventh step in fuzzy TOPSIS, where it is calculated the closeness coefficient for each alternative.
        """

    def _rank_alternatives(self):
        """
        Eight and last step in fuzzy TOPSIS, in which final alternative ranks are calculated as crips values. 
        """

