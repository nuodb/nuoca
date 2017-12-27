# Copyright (c) 2017, NuoDB, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of NuoDB, Inc. nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NUODB, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import click
import socket
import signal
import traceback
import yaml
from nuoca_util import *
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
    NuocaMPTransformPlugin
from nuoca_config import NuocaConfig

nuoca_obj = None

class NuoCA(object):
  """
  NuoDB Collection Agent
  """
  def __init__(self, config_file=None, collection_interval=30,
               plugin_dir=None, starttime=None, mode=None,
               verbose=False, self_test=False, log_level=logging.INFO,
               output_values=None):
    """
    :param config_file: Path to NuoCA configuration file.
    :type config_file: ``str``

    :param collection_interval: Collection Interval in seconds
    :type collection_interval: ``int``

    :param plugin_dir: Path to NuoCA Plugin Directory
    :type plugin_dir: ``str``

    :param starttime: Epoch timestamp of start time of the first collection.
    :type starttime: ``int``, ``None``

    :param mode: Run mode; [coach | insights]
    :type plugin_dir: ``str``

    :param verbose: Flag to indicate printing of verbose messages to stdout.
    :type verbose: ``bool``

    :param self_test: Flag to indicate a 5 loop self test.
    :type self_test: ``bool``

    :param log_level: Python logging level
    :type log_level: ``logging.level``

    :param output_values: list of strings parsable by utils.parse_keyval_list()
    :type output_values: `list` of `str`
    """

    self._starttime = starttime
    if self._starttime:
      # Make sure that starttime is now or in the future.
      current_timestamp = nuoca_gettimestamp()
      if current_timestamp >= self._starttime:
        msg = "starttime must be now or in the future."
        nuoca_log(logging.ERROR, msg)
        raise AttributeError(msg)

    self._nuodb_cfgdir = None
    self.get_nuodb_cfgdir()
    self._nuoca_settings = self.read_nuoca_settings()

    # override default log level
    log_level = self._get_settings_loglevel()

    # collect nuoca.log?
    self._collect_nuoca_log = False
    collect_nuoca_log = self.get_nuoca_settings_value('collect.nuoca.log')
    if collect_nuoca_log:
      self._collect_nuoca_log = True

    # nuoca config file
    self._config = NuocaConfig(config_file)
    self._hostname = socket.gethostname()

    initialize_logger(self._config.NUOCA_LOGFILE, self._collect_nuoca_log)

    nuoca_set_log_level(log_level)
    nuoca_log(logging.INFO, "nuoca server init.")
    self._collection_interval = collection_interval
    if not starttime:
      self._starttime = None
    else:
      self._starttime = int(starttime)
    self._plugin_topdir = plugin_dir
    self._enabled = True
    self._mode = mode
    self._verbose = verbose  # Used to make stdout verbose.
    self._self_test = self_test
    self._output_values = parse_keyval_list(output_values)
    if self._output_values:
      for output_val in self._output_values:
        nuoca_log(logging.INFO, "Output Key: '%s' set to Value: '%s'" %
                  (output_val, self._output_values[output_val]) )

    # The following self._*_plugins are dictionaries of two element
    # tuples in the form: (plugin object, plugin configuration) keyed
    # by the plugin name.
    self._input_plugins = {}
    self._output_plugins = {}
    self._transform_plugins = {}

    if not self._plugin_topdir:
      self._plugin_topdir = os.path.join(get_nuoca_topdir(),
                                         "plugins")
    nuoca_log(logging.INFO, "plugin dir: %s" % self._plugin_topdir)
    input_plugin_dir = os.path.join(self._plugin_topdir, "input")
    output_plugin_dir = os.path.join(self._plugin_topdir, "output")
    transform_plugin_dir = os.path.join(self._plugin_topdir, "transform")
    self._plugin_directories = [input_plugin_dir,
                                output_plugin_dir,
                                transform_plugin_dir]

  def get_nuodb_cfgdir(self):
    if self._nuodb_cfgdir:
      return self._nuodb_cfgdir
    try:
      self._nuodb_cfgdir = os.path.expandvars('$NUODB_CFGDIR')
    except:
      pass
    return self._nuodb_cfgdir

  def read_nuoca_settings(self):
    settings = None
    try:
      if self._nuodb_cfgdir:
        settings_file = os.path.join(self._nuodb_cfgdir, 'nuoca_settings.yml')
        with open(settings_file, 'r') as f:
          settings = yaml.load(f.read())
          print settings
        f.close()
    except:
      pass
    return settings

  def get_nuoca_settings_value(self, variable):
    if not self._nuoca_settings:
      return None
    try:
      value = self._nuoca_settings[variable]
      return value
    except:
      return None

  @property
  def config(self):
    return self._config

  def _get_settings_loglevel(self):
    loglevel = None
    try:
      loglevel_str = self.get_nuoca_settings_value('nuoca.logging.level')
      level_mappings= {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
      }
      loglevel = level_mappings[loglevel_str]
    except:
      pass
    if not loglevel:
      loglevel = logging.INFO
    return loglevel

  def _collection_cycle(self, collection_time):
    """
    _collection_cycle is called at the end of each Collection
    Interval.
    """
    nuoca_log(logging.INFO, "Starting collection interval: %s" %
              collection_time)
    collected_inputs = self._collect_inputs()
    for list_item in collected_inputs:
      list_item['collection_interval'] = self._collection_interval
      if 'timestamp' not in list_item:
        list_item['timestamp'] = collection_time
      list_item['NuoCA.hostname'] = self._hostname
    # TODO Transformations
    self._store_outputs(collected_inputs)

  def _get_activated_input_plugins(self):
    """
    Get a list of "activated" input plugins
    """
    input_list = self.manager.getPluginsOfCategory('Input')
    activated_list = [x for x in input_list if x.is_activated]
    return activated_list

  def _get_deactivated_input_plugins(self):
    """
    Get a list of "deactivated" input plugins
    """
    input_list = self.manager.getPluginsOfCategory('Input')
    deactivated_list = [x for x in input_list if not x.is_activated]
    return deactivated_list

  def _get_activated_output_plugins(self):
    """
    Get a list of "activated" output plugins
    """
    output_list = self.manager.getPluginsOfCategory('Output')
    activated_list = [x for x in output_list if x.is_activated]
    return activated_list

  def _get_deactivated_output_plugins(self):
    """
    Get a list of "activated" output plugins
    """
    output_list = self.manager.getPluginsOfCategory('Output')
    deactivated_list = [x for x in output_list if not x.is_activated]
    return deactivated_list

  def _get_plugin_respose(self, a_plugin):
    """
    Get the response message from the plugin
    :return: Response dictionary if successful, otherwise None.
    """
    plugin_obj = a_plugin.plugin_object
    # noinspection PyBroadException
    try:
      if plugin_obj.child_pipe.poll(self.config.PLUGIN_PIPE_TIMEOUT):
        response = plugin_obj.child_pipe.recv()
        if self._verbose:
          print("%s:%s" % (a_plugin.name, response))
      else:
        nuoca_log(logging.ERROR,
                  "NuoCA._get_plugin_respose: "
                  "Timeout collecting response values from plugin: %s"
                  % a_plugin.name)
        return None

    except Exception as e:
      nuoca_log(logging.ERROR,
                "NuoCA._get_plugin_respose: "
                "Unable to collect response from plugin: %s\n%s"
                % (a_plugin.name, str(e)))
      return None

    # noinspection PyBroadException
    try:
      if not response:
        nuoca_log(logging.ERROR,
                  "NuoCA._get_plugin_respose: "
                  "Missing response from plugin: %s"
                  % a_plugin.name)
        return None
      if 'status_code' not in response:
        nuoca_log(logging.ERROR,
                  "NuoCA._get_plugin_respose: "
                  "status_code missing from plugin response: %s"
                  % a_plugin.name)
        return None

    except Exception as e:
      nuoca_log(logging.ERROR,
                "NuoCA._get_plugin_respose: Error attempting to collect"
                " response from plugin: %s\n%s"
                % (a_plugin.name, str(e)))
      return None

    return response

  def _startup_plugin(self, a_plugin, config=None):
    """
    Send start message to plugin.
    :param a_plugin: The plugin
    :param config: NuoCA Configuration
    :type config: ``dict``
    """
    response = None
    nuoca_log(logging.INFO, "Called to start plugin: %s" % a_plugin.name)
    plugin_msg = {'action': 'startup', 'config': config}
    try:
      a_plugin.plugin_object.child_pipe.send(plugin_msg)
    except Exception as e:
      nuoca_log(logging.ERROR,
                "Unable to send %s message to plugin: %s\n%s"
                % (plugin_msg, a_plugin.name, str(e)))

    try:
      response = self._get_plugin_respose(a_plugin)
    except Exception as e:
      nuoca_log(logging.ERROR,
                "Problem with response on %s message to plugin: %s\n%s"
                % (plugin_msg, a_plugin.name, str(e)))
    if not response or response['status_code'] != 0:
      nuoca_log(logging.ERROR,
                "Disabling plugin that failed to startup: %s"
                % a_plugin.name)
      self.manager.deactivatePluginByName(a_plugin.name, a_plugin.category)
      self._shutdown_plugin(a_plugin)

  @staticmethod
  def _exit_plugin(a_plugin):
    """
    Send Exit message to plugin.
    :param a_plugin: The plugin
    """
    nuoca_log(logging.INFO, "Called to exit plugin: %s" % a_plugin.name)
    plugin_msg = {'action': 'exit'}
    try:
      a_plugin.plugin_object.child_pipe.send(plugin_msg)
    except Exception as e:
      nuoca_log(logging.ERROR,
                "Unable to send %s message to plugin: %s\n%s"
                % (plugin_msg, a_plugin.name, str(e)))

  @staticmethod
  def _shutdown_plugin(a_plugin):
    """
    Send stop message to plugin.

    :param a_plugin: The plugin
    :type a_plugin: NuocaMPPlugin
    """
    nuoca_log(logging.INFO, "Called to shutdown plugin: %s" % a_plugin.name)
    plugin_msg = {'action': 'shutdown'}
    try:
      a_plugin.plugin_object.child_pipe.send(plugin_msg)
    except Exception as e:
      nuoca_log(logging.ERROR,
                "Unable to send %s message to plugin: %s\n%s"
                % (plugin_msg, a_plugin.name, str(e)))

  def _collect_inputs(self):
    """
    Collect time-series data from each activated plugin.
    :return: ``dict`` of time-series data
    """
    # TODO - Use Threads so that we can do concurrent collection.
    plugin_msg = {'action': 'collect',
                  'collection_interval': self._collection_interval}
    rval = []
    activated_plugins = self._get_activated_input_plugins()
    for a_plugin in activated_plugins:
      # noinspection PyBroadException
      try:
        a_plugin.plugin_object.child_pipe.send(plugin_msg)
      except Exception as e:
        nuoca_log(logging.ERROR,
                  "NuoCA._collect_inputs: "
                  "Unable to send %s message to plugin: %s\n%s"
                  % (plugin_msg, a_plugin.name, str(e)))

    for a_plugin in activated_plugins:
      response = self._get_plugin_respose(a_plugin)
      if not response:
        continue
      resp_values = response['resp_values']

      # noinspection PyBroadException
      try:
        if 'collected_values' not in resp_values:
          nuoca_log(logging.ERROR,
                    "NuoCA._collect_inputs: "
                    "'Collected_Values' missing in response from plugin: %s"
                    % a_plugin.name)
          continue
        if not resp_values['collected_values']:
          nuoca_log(logging.DEBUG,
                    "No time-series values were collected from plugin: %s"
                    % a_plugin.name)
          continue
        if type(resp_values['collected_values']) is not list:
          nuoca_log(logging.ERROR,
                    "NuoCA._collect_inputs: "
                    "'Collected_Values' is not a list in "
                    "response from plugin: %s"
                    % a_plugin.name)
          continue

        list_count = len(resp_values['collected_values'])
        for list_index in range(list_count):
          new_values = {}
          key_prefix = a_plugin.name
          collected_dict = resp_values['collected_values'][list_index]
          if 'nuocaCollectionName' in collected_dict:
            key_prefix = collected_dict['nuocaCollectionName']
            del collected_dict['nuocaCollectionName']
          for collected_item in collected_dict:
            key_name = key_prefix + '.' + collected_item
            new_values[key_name] = collected_dict[collected_item]
            if collected_item == 'TimeStamp':
              new_values['timestamp'] = int(collected_dict[collected_item])
            new_values['NuoCA.plugin_name'] = key_prefix
          if self._output_values:
            new_values.update(self._output_values)
          rval.append(new_values)
      except Exception as e:
        nuoca_log(logging.ERROR,
                  "NuoCA._collect_inputs: "
                  "Error attempting to collect"
                  " response from plugin: %s\n%s"
                  % (a_plugin.name, str(e)))

    try:
      deactivated_plugins = self._get_deactivated_input_plugins()
      for a_plugin in deactivated_plugins:
        for a_config in self._config.INPUT_PLUGINS:
          a_config_name = a_config.keys()[0]
          if a_config_name == a_plugin.name:
            self._activate_and_startup_input_plugin(a_config)
      deactivated_plugins = self._get_deactivated_output_plugins()
      for a_plugin in deactivated_plugins:
        for a_config in self._config.OUTPUT_PLUGINS:
          a_config_name = a_config.keys()[0]
          if a_config_name == a_plugin.name:
            self._activate_and_startup_output_plugin(a_config)
    except Exception as e:
      nuoca_log(logging.WARNING,
                "Unable to reactivate deactived plugins during collection: %s"
                % str(e))

    if self._collect_nuoca_log:
      try:
        nuoca_collect_loghandler = get_nuoca_collect_loghandler()
        items = nuoca_collect_loghandler.collect(self._collection_interval)
        for item in items:
          if self._output_values:
            item.update(self._output_values)
          item['NuoCA.plugin_name'] = 'NuoCALog'
          rval.append(item)
      except:
        pass

    return rval

  def _store_outputs(self, collected_inputs):
    if not collected_inputs:
      return
    rval = {}
    plugin_msg = {'action': 'store', 'ts_values': collected_inputs}
    activated_plugins = self._get_activated_output_plugins()
    for a_plugin in activated_plugins:
      # noinspection PyBroadException
      try:
        a_plugin.plugin_object.child_pipe.send(plugin_msg)
      except Exception as e:
        nuoca_log(logging.ERROR,
                  "Unable to send 'Store' message to plugin: %s\n%s"
                  % (a_plugin.name, str(e)))

    for a_plugin in activated_plugins:
      resp_values = self._get_plugin_respose(a_plugin)
      if not resp_values:
        continue

    return rval

  def _create_plugin_manager(self):
    self.manager = MultiprocessPluginManager(
        directories_list=self._plugin_directories,
        plugin_info_ext="multiprocess-plugin")
    self.manager.setCategoriesFilter({
        "Input": NuocaMPInputPlugin,
        "Output": NuocaMPOutputPlugin,
        "Transform": NuocaMPTransformPlugin
    })

  def _activate_and_startup_input_plugin(self, input_plugin):
    input_plugin_name = input_plugin.keys()[0]
    a_plugin = self.manager.getPluginByName(input_plugin_name, 'Input')
    if a_plugin and not a_plugin.is_activated:
      if not self.manager.activatePluginByName(input_plugin_name, 'Input'):
        err_msg = "Cannot activate input plugin: '%s', Skipping." % \
                  input_plugin_name
        nuoca_log(logging.WARNING, err_msg)
      else:
        input_plugin_config = input_plugin.values()[0]
        if not input_plugin_config:
          input_plugin_config = {}
        input_plugin_config['nuoca_start_ts'] = self._starttime
        input_plugin_config['nuoca_collection_interval'] = \
          self._collection_interval
        self._startup_plugin(a_plugin, input_plugin_config)
        self._input_plugins[input_plugin_name] = (a_plugin,
                                                  input_plugin_config)

  def _activate_and_startup_output_plugin(self, output_plugin):
    output_plugin_name = output_plugin.keys()[0]
    a_plugin = self.manager.getPluginByName(output_plugin_name, 'Output')
    if a_plugin and not a_plugin.is_activated:
      if not self.manager.activatePluginByName(output_plugin_name, 'Output'):
        err_msg = "Cannot activate output plugin: '%s', Skipping." % \
                  output_plugin_name
        nuoca_log(logging.WARNING, err_msg)
      else:
        output_plugin_config = output_plugin.values()[0]
        if not output_plugin_config:
          output_plugin_config = {}
        output_plugin_config['nuoca_start_ts'] = self._starttime
        output_plugin_config['nuoca_collection_interval'] = \
          self._collection_interval
        self._startup_plugin(a_plugin, output_plugin_config)
        self._output_plugins[output_plugin_name] = (a_plugin,
                                                  output_plugin_config)

  # Activate plugins and call the plugin's startup() method.
  def _activate_and_startup_plugins(self):
    for input_plugin in self.config.INPUT_PLUGINS:
      self._activate_and_startup_input_plugin(input_plugin)
    for output_plugin in self.config.OUTPUT_PLUGINS:
      self._activate_and_startup_output_plugin(output_plugin)
    # TODO Transform Plugins

  # test if the plugin name is configured in NuoCA.
  def _is_plugin_name_configured(self, name):
    for configured_input in self.config.INPUT_PLUGINS:
      if name in configured_input:
        return True
    for configured_input in self.config.OUTPUT_PLUGINS:
      if name in configured_input:
        return True
    for configured_input in self.config.TRANSFORM_PLUGINS:
      if name in configured_input:
        return True
    return False

  # activate only the NuoCA configured plugins.
  def _activate_configured_plugins(self):
    self.manager.locatePlugins()
    # get a list of ALL plugin candidates
    plugin_candidates = self.manager.getPluginCandidates()
    for candidate in plugin_candidates:
      plugin_configured = self._is_plugin_name_configured(candidate[2].name)
      if not plugin_configured:
        # Remove this plugin candidate because it is no configued by NuoCA
        self.manager.removePluginCandidate(candidate)
    self.manager.loadPlugins()
    self._activate_and_startup_plugins()

  def _shutdown_all_plugins(self):
    for input_plugin in self._input_plugins:
      self.manager.deactivatePluginByName(input_plugin, 'Input')
      a_plugin = self.manager.getPluginByName(input_plugin, 'Input')
      self._shutdown_plugin(a_plugin)
    for output_plugin in self._output_plugins:
      self.manager.deactivatePluginByName(output_plugin, 'Output')
      a_plugin = self.manager.getPluginByName(output_plugin, 'Output')
      self._shutdown_plugin(a_plugin)
    # TODO Transform Plugins

  @staticmethod
  def kill_all_plugin_processes(manager, timeout=5):
    """
    Kill any plugin processes that were left running after waiting up to
    the timeout value..

    :param manager: MultiprocessPluginManager
    :type manager: MultiprocessPluginManager

    :param timeout: Maximum time to wait (in seconds) for the process to
    self exit before killing.
    :type timeout: ``int``

    """
    if not manager:
      return
    all_plugins = manager.getAllPlugins()
    wait_count = timeout
    for a_plugin in all_plugins:
      while a_plugin.plugin_object.proc.is_alive() and wait_count > 0:
        time.sleep(1)
        wait_count -= 1
      if a_plugin.plugin_object.proc.is_alive():
        nuoca_log(logging.INFO, "Killing plugin subprocess: %s" % a_plugin)
        a_plugin.plugin_object.proc.terminate()

  def _remove_all_plugins(self, timeout=5):
    """
    Remove all plugins
    :param timeout: Maximum seconds to wait for subprocess to exit.
    :type timeout: ``int``
    """
    for input_plugin in self._input_plugins:
      a_plugin = self.manager.getPluginByName(input_plugin, 'Input')
      self._exit_plugin(a_plugin)
    for output_plugin in self._output_plugins:
      a_plugin = self.manager.getPluginByName(output_plugin, 'Output')
      self._exit_plugin(a_plugin)
    # TODO Transform Plugins

    # At this point all configured plugin subprocesses should be exiting
    # on their own.  However, if there is any plugin subprocess that didn't
    # exit for any reason, we must terminate them so we don't hang the
    # NuoCA process at exit.
    NuoCA.kill_all_plugin_processes(self.manager, timeout)

  def start(self):
    """
    Startup NuoCA
    """
    self._create_plugin_manager()
    self._activate_configured_plugins()
    interval_sync = IntervalSync(interval=self._collection_interval,
                                 seed_ts=self._starttime)

    # Collection Interval Loop
    loop_count = 0
    while self._enabled:
      loop_count += 1
      collection_timestamp = interval_sync.wait_for_next_interval()
      self._collection_cycle(collection_timestamp * 1000)
      if self._self_test:
        if loop_count >= self._config.SELFTEST_LOOP_COUNT:
          self._enabled = False

  def shutdown(self, timeout=5):
    """
    Shutdown NuoCA
    :param timeout: Maximum seconds to wait for subprocess to exit.
    :type timeout: ``int``
    """
    nuoca_log(logging.INFO, "nuoca server shutdown")
    self._shutdown_all_plugins()
    self._remove_all_plugins(timeout)
    nuoca_logging_shutdown()


def signal_term_handler(signal, frame):
  global nuoca_obj
  if nuoca_obj:
    print "Got SIGTERM"
    sys.exit(0)

def nuoca_run(config_file, collection_interval, plugin_dir,
              starttime, mode, verbose, self_test,
              log_level, output_values):
  global nuoca_obj
  try:
    signal.signal(signal.SIGTERM, signal_term_handler)
    nuoca_obj = NuoCA(config_file, collection_interval, plugin_dir,
                      starttime, mode, verbose, self_test,
                      logging.getLevelName(log_level), output_values)
    nuoca_obj.start()
  except AttributeError as e:
    msg = str(e)
    nuoca_log(logging.ERROR, msg)
    print(msg)
  except Exception as e:
    msg = "Unhandled exception: %s" % e
    nuoca_log(logging.ERROR, msg)
    print(msg)
    stacktrace = traceback.format_exc()
    print(stacktrace)
  finally:
    if nuoca_obj:
      nuoca_obj.shutdown(nuoca_obj.config.SUBPROCESS_EXIT_TIMEOUT)
    print("Done.")


@click.command(help="CONFIG_FILE    path to NuoCA Collection Config file")
@click.argument('config-file', type=str)
@click.option('--collection-interval', default=30,
              help='Collection interval in seconds. Default:30')
@click.option('--plugin-dir', default=None,
              help='Path to NuoCA plugin directory')
@click.option('--starttime', default=None,
              help='Start time in Epoch seconds '
                   'for the first collection interval')
@click.option('--mode', default='coach',
              help='Run mode [coach | insights]')
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.option('--self-test', is_flag=True, default=False,
              help='Run SELFTEST_LOOP_COUNT (default 5) '
                   'collection intervals then exit')
@click.option('--log-level', default='INFO',
              type=click.Choice(['CRITICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG']),
              help='Set log level during test execution.')
@click.option('--output-values',
              '-o',
              multiple=True,
              default=None,
              help='One or more output values as '
                   'key=value pairs separated by commas. Multiples allowed')
def nuoca(config_file, collection_interval, plugin_dir,
          starttime, mode, verbose, self_test, log_level, output_values):
  nuoca_run(config_file, collection_interval, plugin_dir,
            starttime, mode, verbose, self_test, log_level, output_values)

if __name__ == "__main__":
  nuoca(prog_name="nuoca")

