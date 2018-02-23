import base64
import calendar
import os
import signalfx
import time
from botocore.vendored import requests
from collections import namedtuple
from datetime import datetime
from functools import reduce
from itertools import islice, chain
from operator import add

# Constants
DAY_IN_SECONDS = 24 * 60 * 60
STATUSPAGE_BACKFILLED_DAYS = 28
STATUSPAGE_MAX_DATAPOINT_BY_REQUEST = 3000

DataPoint = namedtuple('DataPoint', ['timestamp', 'value'])
TimeFrame = namedtuple('TimeFrame', ['from_timestamp', 'to_timestamp'])


class Config:
    def __init__(self):
        # StatusPage
        self.statuspage_metric_id = os.environ['STATUSPAGE_METRIC_ID']
        statuspage_page_api_endpoint = f'https://api.statuspage.io/v1/pages/{os.environ["STATUSPAGE_PAGE_ID"]}'
        self.statuspage_get_metrics_endpoint = f'{statuspage_page_api_endpoint}/metrics.json'
        self.statuspage_submit_metrics_endpoint = f'{statuspage_page_api_endpoint}/metrics/data.json'
        self.statuspage_headers = {
            "Authorization": "OAuth " + os.environ['STATUSPAGE_API_KEY']
        }

        # SignalFX
        self.signalfx_api_key = os.environ['SIGNALFX_API_KEY']
        self.signalfx_signalflow_program = base64.b64decode(
            os.environ['SIGNALFX_SIGNALFLOW_PROGRAM_BASE64']
        ).decode('utf-8')


def lambda_handler(*_):
    config = Config()
    statuspage_metric = get_statuspage_metric(config)
    time_frame = get_time_frame(statuspage_metric)
    send_signalfx_data_points_to_statuspage(config, collect_signalfx_metrics(config, time_frame))


def get_statuspage_metric(config):
    get_metrics_response = requests.get(config.statuspage_get_metrics_endpoint, headers=config.statuspage_headers)
    get_metrics_response.raise_for_status()

    metric = filter(lambda m: m['id'] == config.statuspage_metric_id, get_metrics_response.json())

    if not metric:
        raise ValueError('Unable to find specified metric on StatusPage.io (Verify the STATUSPAGE_METRIC_ID)')

    return next(metric)


def get_time_frame(statuspage_metric):
    if not statuspage_metric['backfilled']:
        from_timestamp = (int(time.time()) - (STATUSPAGE_BACKFILLED_DAYS * DAY_IN_SECONDS)) * 1000
    elif statuspage_metric['most_recent_data_at']:
        most_recent_data_datetime = datetime.strptime(statuspage_metric['most_recent_data_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        from_timestamp = int(calendar.timegm(most_recent_data_datetime.utctimetuple())) * 1000
    else:
        raise ValueError('No recent data date, yet, it is marked as backfilled')

    return TimeFrame(from_timestamp=from_timestamp, to_timestamp=(int(time.time()) - 60) * 1000)


def collect_signalfx_metrics(config, time_frame):
    with signalfx.SignalFx().signalflow(config.signalfx_api_key) as flow:
        computation = flow.execute(
            config.signalfx_signalflow_program,
            start=time_frame.from_timestamp,
            stop=time_frame.to_timestamp,
            max_delay=1000,
        )
        for msg in filter(lambda x: isinstance(x, signalfx.signalflow.messages.DataMessage), computation.stream()):
            if msg.data and msg.logical_timestamp_ms > time_frame.from_timestamp:
                yield DataPoint(
                    msg.logical_timestamp_ms / 1000,
                    list(msg.data.values())[0],
                )


def send_signalfx_data_points_to_statuspage(config, collected_metrics):
    metrics_sent_total_count = 0
    for metrics_chunk in chunks(collected_metrics, STATUSPAGE_MAX_DATAPOINT_BY_REQUEST):
        statuspage_formated_metrics = {
            config.statuspage_metric_id: list(
                map(lambda d: {'timestamp': d.timestamp, 'value': d.value}, metrics_chunk)
            )
        }

        statuspage_submit_metrics_response = requests.post(
            config.statuspage_submit_metrics_endpoint,
            json={
                'data': statuspage_formated_metrics
            },
            headers=config.statuspage_headers
        )

        try:
            statuspage_submit_metrics_response.raise_for_status()

            metrics_sent_count = reduce(add, [len(metrics) for metrics in list(statuspage_formated_metrics.values())])
            metrics_sent_total_count += metrics_sent_count
            print(
                'Successfully sent {data_points_count} data points from {different_metrics_count} metric(s)'.format(
                    data_points_count=metrics_sent_count,
                    different_metrics_count=len(statuspage_formated_metrics)
                )
            )

        except requests.exceptions.HTTPError as e:
            if 400 <= e.response.status_code < 500:
                raise e  # this is a 4XX error, we should be notified of this error
            else:
                print(e)  # this is a 5XX error, can't do anything about it

    return metrics_sent_total_count > 0


def chunks(iterable, size):
    source_iter = iter(iterable)
    while True:
        batch_iter = islice(source_iter, size)
        yield chain([next(batch_iter)], batch_iter)


if __name__ == '__main__':
    lambda_handler(None, None)
