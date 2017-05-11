import os
import time
import uuid
import hashlib
import logging
from nuoca_config import NuocaConfig


# NuoCA Temp Dir
if not os.path.exists(NuocaConfig.NUOCA_TMPDIR):
  os.mkdir(NuocaConfig.NUOCA_TMPDIR)

# Global NuoCA logger
nuoca_logger = logging.getLogger('nuoca')
loghandler = logging.FileHandler(NuocaConfig.NUOCA_LOGFILE)
loghandler.setLevel(logging.INFO)
loghandler.setFormatter(
  logging.Formatter('%(asctime)s NuoCA %(levelname)s %(message)s'))
nuoca_logger.addHandler(loghandler)

# Global top level directory
nuoca_topdir = None  # Top level directory for NuoCA


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
  :type Python module object

  :param function: Name of the Python function
  :type str

  :return: bool
  """
  import inspect
  return hasattr(module, function) and any(
    function in f for f, _ in inspect.getmembers(
      module, inspect.isroutine))


def resolve_function(module, function):
  """
  Locate specified Python function in the specified Python package.

  :param module: A Python module
  :type Python module object

  :param function: Name of Python function
  :type str

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


def nuoca_set_log_level(log_level):
  """
  Set logging level
  :param log_level: logger log level
  :type: logger level
  """
  global nuoca_logger
  nuoca_logger.setLevel(log_level)


def nuoca_log(log_level, msg):
  """
  Logger message
  :param log_level: logger log level
  :param msg: str: log message
  """
  global nuoca_logger
  nuoca_logger.log(log_level, msg)


def nuoca_logging_shutdown():
  """
  Shutdown ALL logging
  """
  logging.shutdown()


def nuoca_gettimestamp():
  """
  Get the current Epoch time (Unix Timestamp)
  """
  return int(time.time())
