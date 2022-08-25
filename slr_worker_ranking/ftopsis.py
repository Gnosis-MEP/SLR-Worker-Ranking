import numpy as np


class FuzzyTOPSIS(object):
    """
    Class for running the Fuzzy TOPSIS ranking.

    Parameters
    ----------

    Example of input:
    decision_maker_1_decision_matrix = [
        [(9, 10, 10), (9, 10, 10), (9, 10, 10)], # alt1: crit1, 2 and 3 as "very_good_rating"
        [(3, 5, 7), (3, 5, 7), (3, 5, 7)], # alt2: crit1, 2 and 3 as "medium_rating"
    ]
    decision_maker_1_weights = [(0.7, 0.9, 1.0), (0.3, 0.5, 0.7), (0.3, 0.5, 0.7)] # weights for crit1, 2 and 3 as "high_weight", "medium_weight" the last two

    decision_maker_2_decision_matrix = [
        [(3, 5, 7), (3, 5, 7), (3, 5, 7)], # alt1: crit1, 2 and 3 as "medium_rating"
        [(7, 9, 10), (7, 9, 10), (7, 9, 10)], # alt2: crit1, 2 and 3 as "good_rating"
    ]
    decision_maker_2_weights = [(0.3, 0.5, 0.7), (0.5, 0.7, 0.9), (0.5, 0.7, 0.9)] # weights for crit1, 2 and 3 as "medium_weight", "medium_high_weight" the last two

    decision_matrix_list = [decision_maker_1_decision_matrix, decision_maker_2_decision_matrix]
    weights_list = [decision_maker_1_weights, decision_maker_2_weights]
    criteria_benefit_indicator = [True, False, True] # indicates that crit1 and 3 are benefit, and crit 2 is cost.
    """


    def __init__(self, criteria_benefit_indicator):
        self.criteria_benefit_indicator = criteria_benefit_indicator
        self.num_alternatives = None
        self.num_criteria = len(self.criteria_benefit_indicator)
        self.decision_matrix_list = []
        self.criteria_weights_list = []

        self.agg_alt_fuzzy_method = self._defaut_alt_agg_fuzzy_rating_method
        self.agg_crit_fuzzy_method = self._defaut_crit_agg_fuzzy_weight_method
        self.norm_alt_fuzzy_method = self._default_normalize_alternative_method

        self.agg_decision_matrix = None
        self.agg_criteria_weights = None
        self.norm_decision_matrix = None
        self.weighted_norm_decision_matrix = None
        self.FPIS_indexes = None
        self.FNIS_indexes = None

        # self.validate_inputs(alt, k_benefit_crit, k_cost_crit)

        # self.alternatives = alt
        # self.benefit_criteria = k_benefit_crit
        # self.cost_criteria = k_cost_crit

        # self.agg_alternatives = None
        # self.agg_benefit_criteria = None
        # self.agg_cost_criteria = None


    # def validate_inputs(self, alt, k_benefit_crit, k_cost_crit):
    #     assert len(k_benefit_crit) == len(k_cost_crit), "Inconsistent decision makers criteria vectors lenght."
    #     assert len(k_benefit_crit) == len(alt), "Inconsistent decision makers alternatives vectors lenght."


    def add_decision_maker(self, decision_matrix, criteria_weights):
        num_alternatives = len(decision_matrix)
        num_criteria = len(decision_matrix[0])
        if self.num_alternatives is None:
            self.num_alternatives = num_alternatives
        else:
            assert num_alternatives == self.num_alternatives, f"invalid number of alternatives in new decision matrix: {num_alternatives} != {self.num_alternatives}"

        assert num_criteria == self.num_criteria, f"invalid number of criteria in new decision matrix: {num_criteria} != {self.num_criteria}"
        num_criteria_w = len(criteria_weights)
        assert num_criteria_w == self.num_criteria,  f"invalid number of criteria in new criteria weights: {num_criteria_w} != {self.num_criteria}"

        self.decision_matrix_list.append(decision_matrix)
        self.criteria_weights_list.append(criteria_weights)
        self.num_decision_makers = len(self.decision_matrix_list)

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


    def _defaut_alt_agg_fuzzy_rating_method(self, alt_i, crit_j):
        min_left = np.inf
        avg_middle = 0
        max_right = 0
        for dm in self.decision_matrix_list:
            alternative = dm[alt_i]
            criterion = alternative[crit_j]
            c_left, c_middle, c_right = criterion

            min_left = min(min_left, c_left)
            avg_middle += c_middle
            max_right = max(max_right, c_right)
        avg_middle = avg_middle / self.num_decision_makers

        agg_alt_i_crit_j = (min_left, avg_middle, max_right)
        return agg_alt_i_crit_j

    def _all_agg_ratings(self):
        """
            Function used to aggregate the fuzzy ratings for the alternatives for each decision maker
        """
        agg_decision_matrix = []
        for alt_i in range(self.num_alternatives):
            agg_alt_i_criteria = []
            for crit_j in range(self.num_criteria):
                agg_alt_i_crit_j = self.agg_alt_fuzzy_method(alt_i, crit_j)
                agg_alt_i_criteria.append(agg_alt_i_crit_j)

            agg_decision_matrix.append(agg_alt_i_criteria)
        return agg_decision_matrix


    def _defaut_crit_agg_fuzzy_weight_method(self, crit_j):
        # for each decision maker K weight specified for this criteria (initialising with first K)
        min_left_value = np.inf
        avg_middle_value = 0
        max_right_value = 0
        for weights in self.criteria_weights_list:
            criterion_w = weights[crit_j]

            left_value, middle_value, right_value = criterion_w
            min_left_value = min(min_left_value, left_value)
            avg_middle_value += middle_value
            max_right_value = max(max_right_value, right_value)

        avg_middle_value = avg_middle_value / self.num_decision_makers

        return (min_left_value, avg_middle_value, max_right_value)

    def _all_agg_weights(self):
        """
            Function used to aggregate the fuzzy weights for the benefit and
            cost criteria respectivelly
        """

        agg_weights = []
        for crit_j in range(self.num_criteria):
            agg_crit_j = self.agg_crit_fuzzy_method(crit_j)
            agg_weights.append(agg_crit_j)

        return agg_weights

    def _aggregated_ratings_and_weights(self):
        """
        Second step in fuzzy TOPSIS, where the aggregated fuzzy ratings and weights are calculated
        for the criteria and alternatives, respectivelly.
        """
        self.agg_decision_matrix = self._all_agg_ratings()
        self.agg_criteria_weights = self._all_agg_weights()


    def _get_min_left_or_max_right_for_criteria(self, crit_j):
        is_benefit_criterion = self.criteria_benefit_indicator[crit_j]
        final_value = 0
        if is_benefit_criterion is False:
            final_value = np.inf
        # get min/max for cost/benefit criteria
        for alternative in self.agg_decision_matrix:
            criterion = alternative[crit_j]
            left_value, middle_value, right_value = criterion

            if is_benefit_criterion:
                final_value = max(final_value, right_value)
            else:
                final_value = min(final_value, left_value)
        return final_value

    def _default_normalize_alternative_method(self, alt_i, crit_j, minl_or_maxr_criteria):
        alternative = self.agg_decision_matrix[alt_i]
        criterion = alternative[crit_j]
        left_value, middle_value, right_value = criterion

        norm_alt_crit_j = None
        is_benefit_criterion = self.criteria_benefit_indicator[crit_j]
        if is_benefit_criterion:
            norm_alt_crit_j = ((left_value / minl_or_maxr_criteria), (middle_value / minl_or_maxr_criteria), (right_value / minl_or_maxr_criteria))
        else:
            norm_alt_crit_j = ((minl_or_maxr_criteria / right_value), (minl_or_maxr_criteria / middle_value), (minl_or_maxr_criteria / left_value))
        return norm_alt_crit_j

    def _normalized_decision_matrix(self):
        """
        Third step in fuzzy TOPSIS, in which the normalized fuzzy decision matrix is calculated.
        """

        self.norm_decision_matrix = [[None for j in range(self.num_criteria)] for i in range(self.num_alternatives)]
        for crit_j in range(self.num_criteria):
            minl_or_maxr_criteria = self._get_min_left_or_max_right_for_criteria(crit_j)

            for alt_i in range(self.num_alternatives):
                norm_alt_crit_j = self.norm_alt_fuzzy_method(alt_i, crit_j, minl_or_maxr_criteria)
                self.norm_decision_matrix[alt_i][crit_j] = norm_alt_crit_j

    def _weighted_normalized_decision_matrix(self):
        """
        Fourth step in fuzzy TOPSIS, in which the weighted normalized fuzzy decision matrix is calculated.
        """
        self.weighted_norm_decision_matrix = []
        for alternative in self.norm_decision_matrix:
            alt_weighted_norm_criteria = []
            for crit_j, criterion in enumerate(alternative):
                weight_norm_criterion = []
                weight = self.agg_criteria_weights[crit_j]
                for i in range(3):
                    weight_norm_criterion.append(criterion[i] * weight[i])
                alt_weighted_norm_criteria.append(weight_norm_criterion)
            self.weighted_norm_decision_matrix.append(alt_weighted_norm_criteria)

    def _calculate_FPIS_FNIS(self):
        """
        Fifith step in fuzzy TOPSIS, in which the
        Fuzzy Positive Ideal Solution (FPIS) and Fuzzy Negative Ideal Solution (FNIS) are calculated.
        Yuen’s method:
            FPIS: get the max alternative value of each criterion. compare alternatives first based on the right, then middle, then left.
            FNIS: get the min alternative value of each criterion. compare alternatives first based on the left, then middle, then right.
        """
        self.FPIS_indexes = []
        self.FNIS_indexes = []
        for crit_j in range(self.num_criteria):
            fpis = self.weighted_norm_decision_matrix[0][crit_j]
            fpis_alt_i = 0
            fnis = self.weighted_norm_decision_matrix[0][crit_j]
            fnis_alt_i = 0
            for alt_i, alternative in enumerate(self.weighted_norm_decision_matrix):
                criterion = alternative[crit_j]
                found_vi_min = False
                found_vi_max = False

                # compare each fuzzy number value
                for vi_min in range(3):
                    vi_max = 2 - vi_min

                    if not found_vi_max and criterion[vi_max] > fpis[vi_max]:
                        fpis = criterion
                        fpis_alt_i = alt_i
                        found_vi_max = True
                    if not found_vi_min and criterion[vi_min] < fnis[vi_min]:
                        fnis = criterion
                        fnis_alt_i = alt_i
                        found_vi_min = True

            self.FPIS_indexes.append(fpis_alt_i)
            self.FNIS_indexes.append(fnis_alt_i)


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

