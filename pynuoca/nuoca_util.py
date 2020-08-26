# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import datetime
import os
import time
import uuid
import sys
import hashlib
import logging
import logging.handlers
import subprocess
from copy import deepcopy
from logging import Handler
from nuoca_config import NuocaConfig

SECONDS_PER_DAY = 3600 * 24
DEFAULT_SEED_TS = 931752000  # Default NuoCA Epoch Timestamp

# NuoCA Temp Dir
if not os.path.exists(NuocaConfig.NUOCA_TMPDIR):
    os.mkdir(NuocaConfig.NUOCA_TMPDIR)

nuoca_logger = None
nuoca_loghandler = None
nuoca_collect_loghandler = None
yapsy_logger = None
yapsy_loghandler = None
last_log_message = None
last_log_error_message = None

# Global top level directory
nuoca_topdir = None  # Top level directory for NuoCA
nuoca_sourcedir = None

class UTC(datetime.tzinfo):
    """UTC tzinfo"""

    def __init__(self):
        self._zero = datetime.timedelta(0)

    def utcoffset(self, dt):
        return self._zero

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return self._zero


class CollectHandler(Handler):
    def __init__(self):
        self._nuoca_log_collect_queue = []
        Handler.__init__(self)

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        """
        try:
            collect_item = {
                'timestamp': int(record.created * 1000.0),
                'NuoCA.filename': record.filename,
                'NuoCA.funcName': record.funcName,
                'NuoCA.log_level': record.levelname,
                'NuoCA.lineno': record.lineno,
                'NuoCA.message': record.message
            }
            if record.levelno != 20:
                collect_item['NuoCA.pathname'] = record.pathname
                collect_item['NuoCA.process'] = record.process
                collect_item['NuoCA.processName'] = record.processName
                collect_item['NuoCA.thread'] = record.thread
                collect_item['NuoCA.threadName'] = record.threadName
            self._nuoca_log_collect_queue.append(deepcopy(collect_item))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    @property
    def nuoca_log_collect_queue(self):
        return self._nuoca_log_collect_queue

    def collect(self, collection_interval):
        rval = None
        self._collection_interval = collection_interval
        try:
            collection_count = len(self._nuoca_log_collect_queue)
            if not collection_count:
                return rval

            rval = []
            for i in range(collection_count):
                collected_dict = self._nuoca_log_collect_queue.pop(0)
                rval.append(collected_dict)
        except Exception as e:
            pass
        return rval


def get_nuoca_collect_loghandler():
    global nuoca_collect_loghandler
    return nuoca_collect_loghandler


def initialize_logger(nuoca_logfile_name, collect_self=False):
    global nuoca_logger, nuoca_loghandler, nuoca_collect_loghandler
    global yapsy_logger, yapsy_loghandler

    logging.basicConfig(level=logging.INFO)
    # Global NuoCA logger
    nuoca_logger = logging.getLogger('nuoca')
    nuoca_loghandler = logging.handlers.WatchedFileHandler(nuoca_logfile_name)
    nuoca_loghandler.setLevel(logging.INFO)
    nuoca_loghandler.setFormatter(
        logging.Formatter('%(asctime)s NuoCA %(levelname)s %(message)s'))
    nuoca_logger.addHandler(nuoca_loghandler)

    # NuoCA loghandler to turn NuoCA logging events into a NuoCA collected item.
    if collect_self:
        nuoca_collect_loghandler = CollectHandler()
        nuoca_collect_loghandler.setLevel(logging.INFO)
        nuoca_collect_loghandler.setFormatter(
            logging.Formatter('%(asctime)s NuoCA %(levelname)s %(message)s'))
        nuoca_logger.addHandler(nuoca_collect_loghandler)

    # Global Yapsy logger
    yapsy_logger = logging.getLogger('yapsy')
    yapsy_loghandler = logging.FileHandler(nuoca_logfile_name)
    yapsy_loghandler.setLevel(logging.INFO)
    yapsy_loghandler.setFormatter(
        logging.Formatter('%(asctime)s YAPSY %(levelname)s %(message)s'))
    yapsy_logger.addHandler(yapsy_loghandler)
    if collect_self:
        yapsy_logger.addHandler(nuoca_collect_loghandler)


def randomid():
    """
    Returns a unique 32 character string for correlating different log lines.

    :returns str
    """
    # Visually easier in the logs to have a 32 char string without the dashes
    return hashlib.md5(str(uuid.uuid4())).hexdigest()


def function_exists(module, function):
    """
    Check Python module for specificed function.

    :param module: Python module
    :type module: ``types.ModuleType.``

    :param function: Name of the Python function
    :type ``str``

    :return: ``bool``
    """
    import inspect
    return hasattr(module, function) and any(
        function in f for f, _ in inspect.getmembers(
            module, inspect.isroutine))


def resolve_function(module, function):
    """
    Locate specified Python function in the specified Python package.

    :param module: A Python module
    :type module: ``types.ModuleType.``

    :param function: Name of Python function
    :type ``str``

    :return: Function or None if not found.
    """
    func = None
    if function_exists(module, function):
        func = getattr(module, function)
    if not func:
        nuoca_log(logging.ERROR, "Cannot find Python function %s in module %s" % (
            function, module
        ))
    return func


def get_nuoca_topdir():
    """
    Get the NuoCA top level directory

    :return: full path to the NuoCA top level directory.
    :type: str
    """
    global nuoca_topdir
    if not nuoca_topdir:
        this_file = os.path.realpath(__file__)
        this_dir = os.path.dirname(this_file)
        nuoca_topdir = os.path.abspath(os.path.join(this_dir, '..'))
    return nuoca_topdir


def get_nuoca_sourcedir():
    """
    Get the NuoCA python source directory

    :return: full path to the NuoCA python source directory
    :type: str
    """
    global nuoca_sourcedir
    if not nuoca_sourcedir:
        this_file = os.path.realpath(__file__)
        this_dir = os.path.dirname(this_file)
        nuoca_sourcedir = os.path.abspath(this_dir)
    return nuoca_sourcedir


def nuoca_set_log_level(log_level):
    """
    Set logging level
    :param log_level: logger log level
    :type: logger level
    """
    global nuoca_loghandler, yapsy_loghandler
    logging.getLogger('nuoca').setLevel(level=log_level)
    logging.getLogger('yapsy').setLevel(level=log_level)
    nuoca_loghandler.setLevel(log_level)
    if nuoca_collect_loghandler:
        nuoca_collect_loghandler.setLevel(log_level)
    yapsy_loghandler.setLevel(log_level)


def nuoca_log(log_level, msg):
    """
    Logger message
    :param log_level: logger log level
    :param msg: str: log message
    """
    global nuoca_logger, nuoca_loghandler
    global last_log_message, last_log_error_message

    if not msg:
        return

    last_log_message = msg
    if log_level == logging.ERROR:
        last_log_error_message = msg
    if not nuoca_logger:
        if msg[:-1] != '\n':
            msg = msg + '\n'
        sys.stderr.write(msg)
        return
    nuoca_logger.log(log_level, msg)
    nuoca_loghandler.flush()


def nuoca_logging_shutdown():
    """
    Shutdown ALL logging
    """
    logging.shutdown()


def nuoca_get_last_log_message():
    """
    Return last log message
    """
    return last_log_message


def nuoca_get_last_log_error_message():
    """
    Return last log error message
    """
    return last_log_error_message


def nuoca_gettimestamp():
    """
    Get the current Epoch time (Unix Timestamp)
    """
    return int(time.time())


def parse_keyval_list(options):
    """
    Convert list of key/value pairs (typically command line args) to a dict.

    Typically, each element in the list is of the form
        option=value
    However, multiple values may be specified in list elements by separating
    them with a comma (,) as in
        a=1,b=5,c=elbow
    Empty and all whitespace elements are also ignored

    :param options: a list of option values to parse
    :type options: list of str

    :return: dictionary of individual converted options
    :rtype: dict
    """

    ret = {}
    if not options:
        return ret  # ie empty dict

    # Convert -o options to a dict.  -o can be specified multiple times and can
    # have multiple values
    for opt in options:
        opt = opt.strip()
        for elem in opt.split(','):
            if not elem or elem.isspace():
                continue
            if '=' not in elem:
                raise AttributeError("key/value pair {} missing '='".format(elem))
            (k, v) = elem.split('=')
            k = k.strip()
            v = v.strip()
            ret[k] = v
    return ret


def search_running_processes(search_str):
    '''
    Return True if the search_str is in the command of any running process

    :param process_name: Name of process
    :type process_name: ``str``

    :return: True if process name is found, otherwise False
    '''
    try:
        p = subprocess.Popen(["ps", "axo", "comm"], stdout=subprocess.PIPE)
        out, err = p.communicate()
        if (search_str in out):
            return True
    except Exception:
        return False
    return False


def execute_command(command):
    '''
    Execute a posix command

    :param command: command line to execute
    :type command: ``str``

    :return: Python tuple of (exit_code, stdout, stderr)
    '''
    p = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    exit_code = p.returncode
    return (exit_code, stdout, stderr)


def coerce_numeric(s):
    '''
    Convert the string to an integer or float, if it is numeric.
    :param s:
    :type s: ``str``

    :return: integer, or float, or just a string.
    '''
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


class IntervalSync(object):
    """
    IntervalSync

    A universal temporal algorithm that can be used to automatically
    synchronize identical collection intervals across processes or nodes,
    without a predetermined starting timestamp.

    This can be used from cross node synchronization, assuming that the clock
    on all nodes are suitably synchronized (i.e. NTP time synchronization)
    and all nodes use the identical 'interval'.

    There is an optional seed timestamp.  If used, it must be identical for
    all processes/nodes that want to synchronize their intervals.  Clients
    that want to start the collections at specific time, should use seed_ts.

    """

    def __init__(self, interval, seed_ts=None):
        """
        Initialize IntervalSync

        :param interval: time in seconds
         :type ``int``
        :param seed_ts: Optional seed timestamp in UTC epoch seconds.  The
          seed_ts can be a point in the past, or a point in the future.  When
          seed_ts is a point in the future, the next interval will begin at that
          seed_ts.
         :type ``int``
        """
        self._interval = interval
        self._utc_tzinfo = UTC()
        self._seed_ts = seed_ts
        self._unix_epoch = datetime.datetime(1970, 1, 1, tzinfo=self._utc_tzinfo)

        if not self._seed_ts:
            self._seed_ts = DEFAULT_SEED_TS  # default to NuoCA Collection Epoch
        self._seed_dt = datetime.datetime.fromtimestamp(self._seed_ts,
                                                        self._utc_tzinfo)

    def compute_next_interval(self):
        """
        Compute the next time interval.

        :return: datetime object for the next interval.
        """
        now_dt = datetime.datetime.now(self._utc_tzinfo)
        seed_delta = now_dt - self._seed_dt
        seed_delta_total_seconds = seed_delta.total_seconds()
        if seed_delta_total_seconds >= 0:
            elasped_intervals = int(seed_delta_total_seconds) / self._interval
            next_interval = elasped_intervals + 1
            next_interval_seconds_from_seed = next_interval * self._interval
            next_interval_days_delta_from_seed = \
                next_interval_seconds_from_seed / SECONDS_PER_DAY
            next_interval_seconds_delta_from_seed = \
                next_interval_seconds_from_seed - \
                (next_interval_days_delta_from_seed * SECONDS_PER_DAY)
            next_interval_delta = datetime.timedelta(
                days=next_interval_days_delta_from_seed,
                seconds=next_interval_seconds_delta_from_seed)
            next_interval_dt = self._seed_dt + next_interval_delta
        else:
            next_interval_dt = self._seed_dt
        return next_interval_dt

    def wait_for_next_interval(self):
        """
        Wait for the next interval by sleeping until a precise point in time.

        Return UTC timestamp of the interval
        """
        next_interval_dt = self.compute_next_interval()

        # datetime.total_seconds() returns a floating point number
        # with microsecond accuracy.

        next_ts = int((next_interval_dt - self._unix_epoch).total_seconds())
        while True:
            utc_now = datetime.datetime.now(self._utc_tzinfo)
            diff = (next_interval_dt - utc_now).total_seconds()
            if diff <= 0:
                return next_ts
            time.sleep(diff / 2.0)


def to_bool(value):
    valid = {'true': True, 't': True, '1': True,
             'false': False, 'f': False, '0': False,
             }

    if isinstance(value, bool):
        return value

    if not isinstance(value, basestring):
        raise ValueError('invalid literal for boolean. Not a string.')

    lower_value = value.lower()
    if lower_value in valid:
        return valid[lower_value]
    else:
        raise ValueError('invalid literal for boolean: "%s"' % value)
