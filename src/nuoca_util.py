import os
import time
import uuid
import sys
import hashlib
import logging
import subprocess
from nuoca_config import NuocaConfig


# NuoCA Temp Dir
if not os.path.exists(NuocaConfig.NUOCA_TMPDIR):
  os.mkdir(NuocaConfig.NUOCA_TMPDIR)

nuoca_logger = None
nuoca_loghandler = None
yapsy_logger = None
yapsy_loghandler = None

# Global top level directory
nuoca_topdir = None  # Top level directory for NuoCA

def initialize_logger(nuoca_logfile_name):
  global nuoca_logger, nuoca_loghandler
  global yapsy_logger, yapsy_loghandler

  logging.basicConfig(level=logging.INFO)
  # Global NuoCA logger
  nuoca_logger = logging.getLogger('nuoca')
  nuoca_loghandler = logging.FileHandler(nuoca_logfile_name)
  nuoca_loghandler.setLevel(logging.INFO)
  nuoca_loghandler.setFormatter(
    logging.Formatter('%(asctime)s NuoCA %(levelname)s %(message)s'))
  nuoca_logger.addHandler(nuoca_loghandler)

  # Global Yapsy logger
  yapsy_logger = logging.getLogger('yapsy')
  yapsy_loghandler = logging.FileHandler(nuoca_logfile_name)
  yapsy_loghandler.setLevel(logging.INFO)
  yapsy_loghandler.setFormatter(
    logging.Formatter('%(asctime)s YAPSY %(levelname)s %(message)s'))
  yapsy_logger.addHandler(yapsy_loghandler)


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
  yapsy_loghandler.setLevel(log_level)


def nuoca_log(log_level, msg):
  """
  Logger message
  :param log_level: logger log level
  :param msg: str: log message
  """
  global nuoca_logger, nuoca_loghandler
  if not nuoca_logger:
    sys.stderr.write(msg)
    return
  if log_level == logging.ERROR:
    pass
  nuoca_logger.log(log_level, msg)
  nuoca_loghandler.flush()


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
