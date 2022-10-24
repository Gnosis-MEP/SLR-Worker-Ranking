class BaseTOPSIS(object):


    def __init__(self, criteria_benefit_indicator):
        self.criteria_benefit_indicator = criteria_benefit_indicator

    def add_decision_maker(self, decision_matrix, criteria_weights):
        raise NotImplementedError()

    def evaluate(self, validate_first=True):
        raise NotImplementedError()

    def get_alternatives_ranking_scores(self):
        raise NotImplementedError()
