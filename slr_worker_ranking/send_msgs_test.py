#!/usr/bin/env python
import uuid
import json
from event_service_utils.streams.redis import RedisStreamFactory

from slr_worker_ranking.conf import (
    REDIS_ADDRESS,
    REDIS_PORT,
    SERVICE_STREAM_KEY,
    LISTEN_EVENT_TYPE_QUERY_SERVICES_QOS_CRITERIA_RANKED,
    LISTEN_EVENT_TYPE_WORKER_PROFILE_RATED,
)


def make_dict_key_bites(d):
    return {k.encode('utf-8'): v for k, v in d.items()}


def new_msg(event_data):
    event_data.update({'id': str(uuid.uuid4())})
    return {'event': json.dumps(event_data)}


# non_fuzzy_rated_worker = {
#     'worker': {
#         'service_type': 'SomeService',
#         'stream_key': 'some-worker-stream',
#         'queue_limit': 100,
#         'throughput': 6,
#         'accuracy': 3,
#         'energy_consumption': 8,
#         'content_types': ['node_attribute:bounding_box', 'node_attribute:label']
#     }
# }

fuzzy_rated_worker_a = {
    'worker': {
        'service_type': 'SomeService',
        'stream_key': 'some-worker-stream',
        'queue_limit': 100,
        'throughput': (3, 5, 7), # medium_rating
        'accuracy': (1, 3, 5), # low_rating
        'energy_consumption': (7, 9, 10), # High_rating
        'content_types': ['node_attribute:bounding_box', 'node_attribute:label']
    }
}

fuzzy_rated_worker_b = {
    'worker': {
        'service_type': 'SomeService',
        'stream_key': 'other-worker-stream',
        'queue_limit': 100,
        'throughput': (7, 9, 10), # High_rating
        'accuracy': (9, 10, 10), # very_hight_rating
        'energy_consumption': (1, 1, 3), # very_low_rating
        'content_types': ['node_attribute:bounding_box', 'node_attribute:label']
    }
}

fuzzy_rated_worker_c = {
    'worker': {
        'service_type': 'AnotherService',
        'stream_key': 'another-worker-stream',
        'queue_limit': 100,
        'throughput': (3, 5, 7), # medium_rating
        'accuracy': (9, 10, 10), # low_rating
        'energy_consumption': (7, 9, 10), # High_rating
        'content_types': ['node_attribute:bounding_box', 'node_attribute:label']
    }
}

def main():
    stream_factory = RedisStreamFactory(host=REDIS_ADDRESS, port=REDIS_PORT)
    # for checking published events output
    # new_event_type_cmd = stream_factory.create(PUB_EVENT_TYPE_NEW_EVENT_TYPE, stype='streamOnly')

    # for testing sending msgs that the service listens to:
    import ipdb; ipdb.set_trace()
    worker_fuzzy_cmd = stream_factory.create(LISTEN_EVENT_TYPE_WORKER_PROFILE_RATED, stype='streamOnly')

    worker_fuzzy_cmd.write_events(
        new_msg(fuzzy_rated_worker_a)
    )
    worker_fuzzy_cmd.write_events(
        new_msg(fuzzy_rated_worker_b)
    )

    worker_fuzzy_cmd.write_events(
        new_msg(fuzzy_rated_worker_c)
    )

    criteria_rank_cmd = stream_factory.create(LISTEN_EVENT_TYPE_QUERY_SERVICES_QOS_CRITERIA_RANKED, stype='streamOnly')
    import ipdb; ipdb.set_trace()

    criteria_rank_cmd.write_events(
        new_msg(
        {
            'query_id': 'some-query',
            'required_services': ['SomeService', 'AnotherService'],
            'qos_rank': {
                'accuracy': (7, 9, 10),
                'energy_consumption': (9, 10, 10),
                'throughput':(1, 3, 5),
            }
        })
    )
    # read published events output
    # events = new_event_type_cmd.read_events()
    # print(list(events))
    # import ipdb; ipdb.set_trace()


if __name__ == '__main__':
    main()
