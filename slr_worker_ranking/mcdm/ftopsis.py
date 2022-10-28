from os import closerange
import numpy as np

from slr_worker_ranking.mcdm.base import BaseTOPSIS


class FuzzyTOPSIS(BaseTOPSIS):
    """
    Class for running the Fuzzy TOPSIS ranking. Using [1] for the default aggregation methods of alternatives, criteria and normalisation.


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

    Notes
    -----
    Algorithm implemented from  [1]_.

    References
    ----------
    .. [1] Chen, C.T., 2000. Extensions of the TOPSIS for group decision-making under fuzzy environment.
           Fuzzy sets and systems, 114(1), pp.1-9.

    """


    def __init__(self, criteria_benefit_indicator,
                 decision_matrix_list=None, criteria_weights_list=None,
                 agg_alt_fuzzy_method=None, agg_crit_fuzzy_method=None, norm_alt_fuzzy_method=None):
        if decision_matrix_list is None or criteria_weights_list is None:
            decision_matrix_list = []
            criteria_weights_list = []
            num_alternatives = None
            num_decision_makers = None
        else:
            num_alternatives = len(decision_matrix_list[0])
            num_decision_makers = len(decision_matrix_list)

        self.criteria_benefit_indicator = criteria_benefit_indicator
        self.num_alternatives = num_alternatives
        self.num_decision_makers = num_alternatives
        self.num_criteria = len(self.criteria_benefit_indicator)


        self.decision_matrix_list = decision_matrix_list
        self.criteria_weights_list = criteria_weights_list

        self.validate_inputs(criteria_benefit_indicator,decision_matrix_list, criteria_weights_list)

        if agg_alt_fuzzy_method is None:
            agg_alt_fuzzy_method = self._defaut_alt_agg_fuzzy_rating_method
        self.agg_alt_fuzzy_method = agg_alt_fuzzy_method

        if agg_crit_fuzzy_method is None:
            agg_crit_fuzzy_method = self._defaut_crit_agg_fuzzy_weight_method
        self.agg_crit_fuzzy_method = agg_crit_fuzzy_method

        if norm_alt_fuzzy_method is None:
            norm_alt_fuzzy_method = self._default_normalize_alternative_method
        self.norm_alt_fuzzy_method = norm_alt_fuzzy_method

        self.agg_decision_matrix = None
        self.agg_criteria_weights = None
        self.norm_decision_matrix = None
        self.weighted_norm_decision_matrix = None

        self.FPIS_value = None
        # self.FPIS_indexes = None
        self.fpis_distances = None
        self.fpis_distances_per_criterion = None

        self.FNIS_value = None
        # self.FNIS_indexes = None
        self.fnis_distances = None
        self.fnis_distances_per_criterion = None

        self.closeness_coefficients = None
        self.ranking_indexes = None



    def validate_inputs(self, criteria_benefit_indicator, decision_matrix_list, criteria_weights_list):
        assert self.num_criteria > 0, "Number of criteria should be more than zero."

        num_decision_makers = len(decision_matrix_list)
        if num_decision_makers > 0:
            assert num_decision_makers == len(criteria_weights_list), "Inconsistent number of decision makers in criteria weights list input"
            num_alternatives = len(decision_matrix_list[0])
            if self.num_alternatives is None:
                self.num_alternatives = num_alternatives

            for i_dm, dm in enumerate(decision_matrix_list):
                cw = criteria_weights_list[i_dm]
                self._validate_decision_maker(dm, cw)


    def _validate_decision_maker(self, decision_matrix, criteria_weights):
        num_alternatives = len(decision_matrix)
        num_criteria = len(decision_matrix[0])
        if self.num_alternatives is not None:
            assert num_alternatives == self.num_alternatives, f"invalid number of alternatives in decision matrix: {num_alternatives} != {self.num_alternatives}"

        assert num_criteria == self.num_criteria, f"invalid number of criteria in decision matrix: {num_criteria} != {self.num_criteria}"
        num_criteria_w = len(criteria_weights)
        assert num_criteria_w == self.num_criteria,  f"invalid number of criteria in criteria weights: {num_criteria_w} != {self.num_criteria}"


    def add_decision_maker(self, decision_matrix, criteria_weights):
        if self.num_alternatives is None:
            num_alternatives = len(decision_matrix)
            self.num_alternatives = num_alternatives
        self._validate_decision_maker(decision_matrix, criteria_weights)

        self.decision_matrix_list.append(decision_matrix)
        self.criteria_weights_list.append(criteria_weights)
        self.num_decision_makers = len(self.decision_matrix_list)

    def evaluate(self, validate_first=True):
        if validate_first:
            self.validate_inputs(self.criteria_benefit_indicator, self.decision_matrix_list, self.criteria_weights_list)

        self._aggregated_ratings_and_weights()
        self._normalized_decision_matrix()
        self._weighted_normalized_decision_matrix()
        self._calculate_FPIS_FNIS()
        self._distance_from_FPIS_FNIS()
        self._calculate_closeness_coefficients()
        self._rank_alternatives()
        return self.ranking_indexes


    def _defaut_alt_agg_fuzzy_rating_method(self, alt_i, crit_j):
        """
            Same method for aggregating fuzzy ratings used in Chen [1].
            Returns the avg of each individual value in the triangular fuzzy number
        """
        avg_left = 0
        avg_middle = 0
        avg_right = 0
        for dm in self.decision_matrix_list:
            alternative = dm[alt_i]
            criterion = alternative[crit_j]
            c_left, c_middle, c_right = criterion

            avg_left += c_left
            avg_middle += c_middle
            avg_right += c_right
        avg_left = avg_left / self.num_decision_makers
        avg_middle = avg_middle / self.num_decision_makers
        avg_right = avg_right / self.num_decision_makers

        agg_alt_i_crit_j = [avg_left, avg_middle, avg_right]
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
        avg_left_value = 0
        avg_middle_value = 0
        avg_right_value = 0
        for weights in self.criteria_weights_list:
            criterion_w = weights[crit_j]

            left_value, middle_value, right_value = criterion_w
            avg_left_value += left_value
            avg_middle_value += middle_value
            avg_right_value += right_value

        avg_left_value = avg_left_value / self.num_decision_makers
        avg_middle_value = avg_middle_value / self.num_decision_makers
        avg_right_value = avg_right_value / self.num_decision_makers

        return [avg_left_value, avg_middle_value, avg_right_value]

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
        Chen’s method:
            FPIS: (1, 1, 1)... simplification where positive and negative ideal are an alternative with 1s and 0s respectivelly
            FNIS: (0, 0, 0)...
        """
        self.FPIS_value = []
        self.FNIS_value = []
        for crit_j in range(self.num_criteria):
            fpis = [1, 1, 1]
            fnis = [0, 0, 0]
            self.FPIS_value.append(fpis)
            self.FNIS_value.append(fnis)


    def _fuzzy_number_distance_calculation(self, val1, val2):
        "euclidian distance of two triangular fuzzy numbers proposed by Chen, C.T., 2000"
        first_part = 0
        for vi in range(3):
            first_part += (val1[vi] - val2[vi])**2
        second_part = first_part / 3
        third_part = np.sqrt(second_part)
        return third_part


    def _calculate_distance_from_ideal_solutions(self, alt_i, crit_j, is_positive=True):
        if is_positive:
            # ideal_solution_index = self.FPIS_indexes[crit_j]
            ideal_solution = self.FPIS_value
        else:
            ideal_solution = self.FNIS_value
            # ideal_solution_index = self.FNIS_indexes[crit_j]
        ideal_criterion = ideal_solution[crit_j]
        criterion = self.weighted_norm_decision_matrix[alt_i][crit_j]
        dist = 0
        # if any(alt_i[i] != ideal_solution[i] for i in range(self.num_criteria):
        dist = self._fuzzy_number_distance_calculation(criterion, ideal_criterion)
        return dist

    def _distance_from_FPIS_FNIS(self):
        """
        Sixth step in fuzzy TOPSIS, where the distances from each alternative to the
        Fuzzy Positive Ideal Solution (FPIS) and Fuzzy Negative Ideal Solution (FNIS) are calculated.
        """
        self.fpis_distances = []
        self.fpis_distances_per_criterion = []
        self.fnis_distances = []
        self.fnis_distances_per_criterion = []
        for alt_i, alternative in enumerate(self.weighted_norm_decision_matrix):
            alt_fpis_distances = []
            alt_fnis_distances = []
            for crit_j, criterion in enumerate(alternative):
                fpis_dist = self._calculate_distance_from_ideal_solutions(alt_i, crit_j, is_positive=True)
                fnis_dist = self._calculate_distance_from_ideal_solutions(alt_i, crit_j, is_positive=False)

                alt_fpis_distances.append(fpis_dist)
                alt_fnis_distances.append(fnis_dist)

            self.fpis_distances_per_criterion.append(alt_fpis_distances)
            self.fpis_distances.append(sum(alt_fpis_distances))
            self.fnis_distances_per_criterion.append(alt_fnis_distances)
            self.fnis_distances.append(sum(alt_fnis_distances))

    def _calculate_closeness_coefficients(self):
        """
        Seventh step in fuzzy TOPSIS, where it is calculated the closeness coefficient for each alternative.
        """
        self.closeness_coefficients = []
        for alt_j in range(self.num_alternatives):
            nominator = self.fnis_distances[alt_j]
            denominator = self.fnis_distances[alt_j] + self.fpis_distances[alt_j]
            close_coeff = nominator / denominator
            self.closeness_coefficients.append(close_coeff)

    def get_alternatives_ranking_scores(self):
        return self.closeness_coefficients

    def _rank_alternatives(self):
        """
        Eight and last step in fuzzy TOPSIS, in which final alternative ranks are calculated as crips values.
        """

        self.ranking_indexes = sorted(range(self.num_alternatives), key=lambda k: self.closeness_coefficients[k], reverse=True)




class AltFuzzyTOPSIS(FuzzyTOPSIS):

    def __init__(self, criteria_benefit_indicator,
                 decision_matrix_list=None, criteria_weights_list=None,
                 agg_alt_fuzzy_method=None, agg_crit_fuzzy_method=None, norm_alt_fuzzy_method=None):

        super(AltFuzzyTOPSIS, self).__init__(criteria_benefit_indicator,
            decision_matrix_list, criteria_weights_list,
            agg_alt_fuzzy_method, agg_crit_fuzzy_method, norm_alt_fuzzy_method)

        # if agg_alt_fuzzy_method is None:
        #     agg_alt_fuzzy_method = self._defaut_alt_agg_fuzzy_rating_method
        # self.agg_alt_fuzzy_method = agg_alt_fuzzy_method

        # if agg_crit_fuzzy_method is None:
        #     agg_crit_fuzzy_method = self._defaut_crit_agg_fuzzy_weight_method
        # self.agg_crit_fuzzy_method = agg_crit_fuzzy_method

        # if norm_alt_fuzzy_method is None:
        #     norm_alt_fuzzy_method = self._default_normalize_alternative_method
        # self.norm_alt_fuzzy_method = norm_alt_fuzzy_method

        self.FPIS_indexes = None
        self.FNIS_indexes = None

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

        agg_alt_i_crit_j = [min_left, avg_middle, max_right]
        return agg_alt_i_crit_j

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



    def _calculate_distance_from_ideal_solutions(self, alt_i, crit_j, is_positive=True):
        ideal_solution_index = self.FPIS_indexes[crit_j]
        if not is_positive:
            ideal_solution_index = self.FNIS_indexes[crit_j]

        criterion = self.weighted_norm_decision_matrix[alt_i][crit_j]
        dist = 0
        if alt_i != ideal_solution_index:
            ideal_solution = self.weighted_norm_decision_matrix[ideal_solution_index][crit_j]
            dist = self._fuzzy_number_distance_calculation(criterion, ideal_solution)
        return dist