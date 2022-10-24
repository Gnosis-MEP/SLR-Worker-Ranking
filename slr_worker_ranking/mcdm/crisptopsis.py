import skcriteria as skc
from skcriteria.preprocessing import invert_objectives, scalers
from skcriteria.pipeline import mkpipe
from skcriteria.madm.similarity import TOPSIS as SKC_TOPSIS

from slr_worker_ranking.mcdm.base import BaseTOPSIS

class CrispTOPSIS(BaseTOPSIS):
    "interface class to scikit-criteria topsis"

    def __init__(self, criteria_benefit_indicator):
        self.setup_skc_objectives(criteria_benefit_indicator)
        self.skc_dm = None
        ranker_pipe = mkpipe(
            invert_objectives.NegateMinimize(),
            scalers.VectorScaler(target="matrix"),  # this scaler transform the matrix
            scalers.SumScaler(target="weights"),  # and this transform the weights
            SKC_TOPSIS(),
        )
        self.skc_ranker = ranker_pipe
        self.skc_result = None


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
        self.ranking_indexes = sorted(
            range(self.skc_result.alternatives.size),
            key=lambda k: self.skc_result.rank_[k],
            reverse=False
        )
        return self.ranking_indexes

    def get_alternatives_ranking_scores(self):
        if self.skc_result is None:
            return None

        return self.skc_result.e_['similarity'].tolist()