import collections
import itertools
import re

import psutil
from loguru import logger

ProcessFilterPredicate = collections.namedtuple('ProcessFilterPredicate', ['name', 'conditions'])


def _match_process(process, predicate):
    name, regex = predicate

    value = getattr(process, name)
    # If this attribute is a function, call it to get the value
    try:
        value = value()
    except TypeError:
        pass

    # Convert all values to strings so we can match them with a RegEx
    if isinstance(value, int):
        value = str(value)
    elif isinstance(value, (list, tuple)):
        value = ' '.join(value)

    return bool(re.match(regex, value))


def get_net_connections():
    return psutil.net_connections()


def filter_net_connections(predicates):
    filtered = collections.defaultdict(list)
    connections = get_net_connections()
    for connection, predicate in itertools.product(connections, predicates):
        # Stop no specified conditions from matching every process
        if not (predicate.conditions and connection.pid):
            continue

        try:
            process = psutil.Process(connection.pid)
        except psutil.NoSuchProcess:
            logger.warning('Process with PID {} died while filtering network connections', connection.pid)
            continue

        if all(_match_process(process, condition) for condition in predicate.conditions):
            filtered[predicate.name].append(connection)

    return filtered
