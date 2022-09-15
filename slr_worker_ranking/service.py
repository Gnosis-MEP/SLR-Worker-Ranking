from re import S
import threading

from event_service_utils.logging.decorators import timer_logger
from event_service_utils.services.event_driven import BaseEventDrivenCMDService
from event_service_utils.tracing.jaeger import init_tracer

from slr_worker_ranking.mcdm.ftopsis import FuzzyTOPSIS
from slr_worker_ranking.conf import (
    LISTEN_EVENT_TYPE_WORKER_PROFILE_RATED,
    LISTEN_EVENT_TYPE_QUERY_SERVICES_QOS_CRITERIA_RANKED,
    PUB_EVENT_TYPE_SERVICE_SLR_PROFILES_RANKED
)


class SLRWorkerRanking(BaseEventDrivenCMDService):
    def __init__(self,
                 service_stream_key, service_cmd_key_list,
                 pub_event_list, service_details,
                 stream_factory,
                 ranker_type,
                 ranker_criteria,
                 logging_level,
                 tracer_configs):
        tracer = init_tracer(self.__class__.__name__, **tracer_configs)
        super(SLRWorkerRanking, self).__init__(
            name=self.__class__.__name__,
            service_stream_key=service_stream_key,
            service_cmd_key_list=service_cmd_key_list,
            pub_event_list=pub_event_list,
            service_details=service_details,
            stream_factory=stream_factory,
            logging_level=logging_level,
            tracer=tracer,
        )
        self.cmd_validation_fields = ['id']
        self.data_validation_fields = ['id']
        self.ranker_criteria = ranker_criteria
        self.ranker_type = ranker_type
        self.ranker = None
        self.initialize_ranker()
        self.alternatives_by_service_type = {}
        self.query_slr_profiles_map = {}
        # self.query_criteria_weights_profile = {
        #     'query1': [],
        # }
        self.slr_profiles_by_service = {}
        # self.slr_profile_rankings = {}



    def initialize_ranker(self):
        ranker_type_class_map = {
            'chen-ftopsis': FuzzyTOPSIS
        }
        ranker_cls = ranker_type_class_map[self.ranker_type]
        self.ranker = ranker_cls(criteria_benefit_indicator=list(self.ranker_criteria.values()))

    def publish_service_slr_profiles_ranked(self, service_type):
        slr_profiles = self.slr_profiles_by_service.get(service_type, None)
        if slr_profiles:
            new_event_data = {
                'id': self.service_based_random_event_id(),
                'service_type': service_type,
                'slr_profiles': slr_profiles,
            }
            self.publish_event_type_to_stream(event_type=PUB_EVENT_TYPE_SERVICE_SLR_PROFILES_RANKED, new_event_data=new_event_data)

    def get_slr_profile_id_from_service_type_and_criteria_weights(self, service_type, criteria_weights):
        criterias_str = '-'.join([f'{cw}' for cw in criteria_weights])
        slr_id = f'{service_type}-{criterias_str}'
        return slr_id

    # def get_ranked_alternatives(self, service_alternatives, ranking_index):
    #     ranked_alternatives = []
    #     alternatives_index_to_id = {i: k for i, k in enumerate(service_alternatives.keys())}
    #     for i in ranking_index:
    #         ranked_alternatives.append(alternatives_index_to_id[i])
    #     return ranked_alternatives

    def update_slr_profile_rankings_of_service_type(self, service_type):
        "inefficient, should only update the profiles that are missing or update all profiles of a type that changed (new worker)"
        service_slr_profiles = self.slr_profiles_by_service.get(service_type, None)
        if service_slr_profiles is not None:
            for slr_profile_id, slr_profile in service_slr_profiles.items():
                service_alternatives = self.alternatives_by_service_type[service_type]
                decision_matrix = list(service_alternatives.values())
                criteria_weights = slr_profile['criteria_weights']
                # import ipdb;ipdb.set_trace()
                ranking_index = [0]
                ranking_scores = [0]
                if len(decision_matrix) > 1:
                    # for query, criteria_weights_profile in self.query_criteria_weights_profile.items():
                    self.initialize_ranker()
                    self.ranker.add_decision_maker(decision_matrix=decision_matrix, criteria_weights=criteria_weights)
                    ranking_index = self.ranker.evaluate()
                    ranking_scores = self.ranker.get_alternatives_ranking_scores()
                slr_profile['alternatives_ids'] = list(service_alternatives.keys())
                slr_profile['ranking_index'] = ranking_index
                slr_profile['ranking_scores'] = ranking_scores
                # slr_ranked_alternatives = self.get_ranked_alternatives(service_alternatives, ranking_index)
                # slr_profile['ranked_alternatives'] = slr_ranked_alternatives
            self.publish_service_slr_profiles_ranked(service_type)

    def get_alternative_from_rated_worker(self, rated_worker):
        return [rated_worker[k] for k in self.ranker_criteria.keys()]

    def process_worker_profile_rated(self, rated_worker):
        # rated_worker = {
        #     'service_type': SERVICE_DETAILS_SERVICE_TYPE,
        #     'stream_key': SERVICE_DETAILS_STREAM_KEY,
        #     'throughput': SERVICE_DETAILS_THROUGHPUT,
        #     'accuracy': SERVICE_DETAILS_ACCURACY,
        #     'energy_consumption': SERVICE_DETAILS_ENERGY_CONSUMPTION,
        # }
        stream_key = rated_worker['stream_key']
        service_type = rated_worker['service_type']
        if stream_key in self.alternatives_by_service_type.get(service_type, {}).keys():
            self.logger.warning('Duplicated rated worker stream key. Will ignored new one in favor of the previous.')
            return
        service_alternatives = self.alternatives_by_service_type.setdefault(service_type, {})
        service_alternatives[stream_key] = self.get_alternative_from_rated_worker(rated_worker)
        self.update_slr_profile_rankings_of_service_type(service_type)

    def process_query_services_qos_criteria_ranked(self, event_data):
        query_id = event_data['query_id']
        # event_data = {
        #     'query_id': '...',
        #     'required_services': ['s1', 's2'],
        #     'qos_rank': {
        #         'energy_consumption': 1,
        #         'throughput': [1, 2, 3], # if fuzzy
        #     }
        # }
        if query_id not in self.query_slr_profiles_map:
            criteria_weights = [event_data['qos_rank'][k] for k in self.ranker_criteria]
            required_services = event_data['required_services']
            for service_type in required_services:
                slr_profile_id = self.get_slr_profile_id_from_service_type_and_criteria_weights(service_type, criteria_weights)
                service_slr_profiles = self.slr_profiles_by_service.setdefault(service_type, {})
                is_new_profile = slr_profile_id not in service_slr_profiles.keys()

                slr_profile = service_slr_profiles.setdefault(
                    slr_profile_id,
                    {'query_ids': [], 'criteria_weights': criteria_weights}
                )
                slr_profile['query_ids'].append(query_id)
                self.query_slr_profiles_map.setdefault(query_id, set()).add(slr_profile_id)
                if is_new_profile:
                    self.update_slr_profile_rankings_of_service_type(service_type)
        else:
            self.logger.warning('Duplicated query id. Will ignored new one in favor of the previous.')
            return

    @timer_logger
    def process_event_type(self, event_type, event_data, json_msg):
        if not super(SLRWorkerRanking, self).process_event_type(event_type, event_data, json_msg):
            return False

        if event_type == LISTEN_EVENT_TYPE_QUERY_SERVICES_QOS_CRITERIA_RANKED:
            self.process_query_services_qos_criteria_ranked(event_data)

        if event_type == LISTEN_EVENT_TYPE_WORKER_PROFILE_RATED:
            rated_worker = event_data['worker']
            self.process_worker_profile_rated(rated_worker)


    def log_state(self):
        super(SLRWorkerRanking, self).log_state()
        self.logger.info(f'Service name: {self.name}')
        self.logger.info(f'Ranker Type: {self.ranker_type}')
        self._log_dict('Ranker Criteria', self.ranker_criteria)
        self._log_dict('Alternatives by Service Type', self.alternatives_by_service_type)
        self._log_dict('Query SLR Profile ID', self.query_slr_profiles_map)
        self._log_dict('SLR Profiles (by Service Type)', self.slr_profiles_by_service)

    def run(self):
        super(SLRWorkerRanking, self).run()
        self.log_state()
        self.run_forever(self.process_cmd)