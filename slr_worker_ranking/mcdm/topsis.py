import skcriteria as skc
from skcriteria.madm.similarity import TOPSIS as SKC_TOPSIS

from slr_worker_ranking.mcdm.base import BaseTOPSIS

class CrispTOPSIS(BaseTOPSIS):
    "interface class to scikit-criteria topsis"

    def __init__(self, criteria_benefit_indicator):
        self.setup_skc_objectives(criteria_benefit_indicator)
        self.skc_dm = None
        self.skc_ranker = SKC_TOPSIS()
        pass


    def setup_skc_objectives(self, criteria_benefit_indicator):
        self.skc_objectives = [max if c else min for c in criteria_benefit_indicator]

    def add_decision_maker(self, decision_matrix, criteria_weights):
        self.skc_dm = skc.mkdm(
            matrix=decision_matrix,
            objectives=self.skc_objectives,
            weights=criteria_weights
        )

    def evaluate(self, validate_first=True):
        self.skc_result = self.skc_ranker.evaluate(self.skc_dm)
        return self.skc_result

    def get_alternatives_ranking_scores(self):
        pass