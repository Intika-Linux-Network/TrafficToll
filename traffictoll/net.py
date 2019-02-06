import collections
import itertools
import re

import psutil
from loguru import logger

ProcessFilterPredicate = collections.namedtuple('ProcessFilterPredicate', ['name', 'conditions'])


def _match_process(process, predicate):
    name, regex = predicate
    value = getattr(process, name)()
    if isinstance(value, int):
        value = str(value)
    elif isinstance(value, (list, tuple)):
        value = ' '.join(value)

    return bool(re.match(regex, value))


def filter_net_connections(predicates):
    connections = psutil.net_connections()
    filtered = collections.defaultdict(list)
    for connection, predicate in itertools.product(connections, predicates):
        if not connection.pid:
            continue

        try:
            process = psutil.Process(connection.pid)
        except psutil.NoSuchProcess:
            logger.warning('Process with PID {} died while filtering network connections', connection.pid)
            continue

        if all(_match_process(process, condition) for condition in predicate.conditions):
            filtered[predicate.name].append(connection)

    return filtered
