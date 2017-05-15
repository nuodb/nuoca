import click
import json
import traceback
from nuoca_util import *
from yapsy.MultiprocessPluginManager import MultiprocessPluginManager
from nuoca_plugin import NuocaMPInputPlugin, NuocaMPOutputPlugin, \
  NuocaMPTransformPlugin
from nuoca_config import NuocaConfig


class NuoCA(object):
  """
  NuoDB Collection Agent
  """
  def __init__(self, config_file=None, collection_interval=30,
               plugin_dir=None, starttime=None, verbose=False,
               self_test=False, log_level=logging.INFO):
    """
    :param config_file: Path to NuoCA configuration file.
    :type config_file: ``str``

    :param collection_interval: Collection Interval in seconds
    :type collection_interval: ``int``

    :param plugin_dir: Path to NuoCA Plugin Directory
    :type plugin_dir: ``str``

    :param starttime: Epoch timestamp of start time of the first collection.
    :type starttime: ``int``

    :param verbose: Flag to indicate printing of verbose messages to stdout.
    :type verbose: ``bool``

    :param verbose: Flag to indicate a 5 loop self test.
    :type verbose: ``bool``
    """
    self._config = NuocaConfig(config_file)

    nuoca_set_log_level(log_level)
    nuoca_log(logging.INFO, "nuoca server init.")
    self._collection_interval = collection_interval
    self._starttime = starttime
    self._plugin_topdir = plugin_dir
    self._enabled = True
    self._verbose = verbose  # Used to make stdout verbose.
    self._self_test = self_test

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

  @property
  def config(self):
    return self._config

  def _collection_cycle(self, endtime):
    """
    _collection_cycle is called at the end of each Collection
    Interval.
    """
    nuoca_log(logging.INFO, "Starting collection interval: %s" % endtime)
    collected_inputs = self._collect_inputs()
    collected_inputs['collection_interval'] = self._collection_interval
    collected_inputs['timestamp'] = endtime
    # TODO Transformations
    self._store_outputs(collected_inputs)

  def _get_activated_input_plugins(self):
    """
    Get a list of "activated" input plugins
    """
    input_list = self.manager.getPluginsOfCategory('Input')
    activated_list = [x for x in input_list if x.is_activated]
    return activated_list

  def _get_activated_output_plugins(self):
    """
    Get a list of "activated" output plugins
    """
    output_list = self.manager.getPluginsOfCategory('Output')
    activated_list = [x for x in output_list if x.is_activated]
    return activated_list

  def _get_plugin_respose(self, a_plugin):
    """
    Get the response message from the plugin
    :return: Response dictionary if successful, otherwise None.
    """
    response = None
    plugin_obj = a_plugin.plugin_object
    # noinspection PyBroadException
    try:
      if plugin_obj.child_pipe.poll(self.config.PLUGIN_PIPE_TIMEOUT):
        response = plugin_obj.child_pipe.recv()
        if self._verbose:
          print("%s:%s" % (a_plugin.name, response))
      else:
        nuoca_log(logging.ERROR,
                  "Timeout collecting response values from plugin: %s"
                  % a_plugin.name)
        return None

    except Exception as e:
      nuoca_log(logging.ERROR,
                "Unable to collect response from plugin: %s\n%s"
                % (a_plugin.name, str(e)))
      return None

    # noinspection PyBroadException
    try:
      if not response:
        nuoca_log(logging.ERROR,
                  "Missing response from plugin: %s"
                  % a_plugin.name)
        return None
      if not 'status_code' in response:
        nuoca_log(logging.ERROR,
                  "status_code missing from plugin response: %s"
                  % a_plugin.name)
        return None

    except Exception as e:
      nuoca_log(logging.ERROR,
                "Error attempting to collect"
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
    if response['status_code'] != 0:
      nuoca_log(logging.ERROR,
                "Disabling plugin that failed to startup: %s"
                % a_plugin.name)
      self.manager.deactivatePluginByName(a_plugin.name, a_plugin.category)
      self._shutdown_plugin(a_plugin)

  def _exit_plugin(self, a_plugin):
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

  def _shutdown_plugin(self, a_plugin):
    """
    Send stop message to plugin.
    :param a_plugin: The plugin
    :param config: NuoCA Configuration
    :type config: ``dict``
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
    rval = {}
    resp_values = None
    activated_plugins = self._get_activated_input_plugins()
    for a_plugin in activated_plugins:
      # noinspection PyBroadException
      try:
        a_plugin.plugin_object.child_pipe.send(plugin_msg)
      except Exception as e:
        nuoca_log(logging.ERROR,
                  "Unable to send %s message to plugin: %s\n%s"
                  % (plugin_msg, a_plugin.name, str(e)))

    for a_plugin in activated_plugins:
      resp_values = None
      plugin_obj = a_plugin.plugin_object
      response = self._get_plugin_respose(a_plugin)
      if not response:
        continue
      resp_values = response['resp_values']

      # noinspection PyBroadException
      try:
        if 'collected_values' not in resp_values:
          nuoca_log(logging.ERROR,
                    "'Collected_Values' missing in response from plugin: %s"
                    % a_plugin.name)
          continue
        rval.update(resp_values['collected_values'])
      except Exception as e:
        nuoca_log(logging.ERROR,
                  "Error attempting to collect"
                  " response from plugin: %s\n%s"
                  % (a_plugin.name, str(e)))
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
      plugin_obj = a_plugin.plugin_object
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

  def _load_all_plugins(self):
    self.manager.collectPlugins()
    for input_plugin in self.config.INPUT_PLUGINS:
      input_plugin_name = input_plugin.keys()[0]
      if not self.manager.activatePluginByName(input_plugin_name, 'Input'):
        err_msg = "Cannot activate input plugin: '%s', Skipping." % \
                  input_plugin_name
        nuoca_log(logging.WARNING, err_msg)
      else:
        a_plugin = self.manager.getPluginByName(input_plugin_name, 'Input')
        if a_plugin:
          input_plugin_config = input_plugin.values()[0]
          self._startup_plugin(a_plugin, input_plugin_config)
          self._input_plugins[input_plugin_name] = (a_plugin,
                                                    input_plugin_config)

    for output_plugin in self.config.OUTPUT_PLUGINS:
      output_plugin_name = output_plugin.keys()[0]
      if not self.manager.activatePluginByName(output_plugin_name, 'Output'):
        err_msg = "Cannot activate output plugin: '%s', Skipping." % \
                  output_plugin_name
        nuoca_log(logging.WARNING, err_msg)
      else:
        a_plugin = self.manager.getPluginByName(output_plugin_name, 'Output')
        if a_plugin:
          output_plugin_config = output_plugin.values()[0]
          self._startup_plugin(a_plugin, output_plugin_config)
          self._output_plugins[output_plugin_name] = (a_plugin,
                                                      output_plugin_config)
    # TODO Transform Plugins

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
    all_plugins = self.manager.getAllPlugins()
    wait_count = timeout  # maximum seconds to wait for processes
                          # to exit on their own
    for a_plugin in all_plugins:
      while a_plugin.plugin_object.proc.is_alive() and wait_count > 0:
        time.sleep(1)
        wait_count -= 1
      if a_plugin.plugin_object.proc.is_alive():
        nuoca_log(logging.INFO, "Killing plugin subprocess: %s" % a_plugin)
        a_plugin.plugin_object.proc.terminate()

  def start(self):
    """
    Startup NuoCA
    """
    self._create_plugin_manager()
    self._load_all_plugins()

    # Find the start of the next time interval
    current_timestamp = nuoca_gettimestamp()
    next_interval_time = current_timestamp
    if self._starttime:
      if current_timestamp >= self._starttime:
        msg = "starttime must be in the future."
        nuoca_log(logging.ERROR, msg)
        raise AttributeError(msg)
      next_interval_time = self._starttime

    # Collection Interval Loop
    loop_count = 0
    while self._enabled:
      loop_count += 1
      current_timestamp = nuoca_gettimestamp()
      waittime = next_interval_time - current_timestamp
      if waittime > 0:
        time.sleep(waittime)
      next_interval_time += self._collection_interval
      self._collection_cycle(next_interval_time)
      if self._self_test:
        if loop_count >= self._config.SELFTEST_LOOP_COUNT:
          self._enabled = False

  # noinspection PyMethodMayBeStatic
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


def nuoca_run(config_file, collection_interval, plugin_dir,
              starttime, verbose, self_test,
              log_level):
  nuoca_obj = None
  try:
    nuoca_obj = NuoCA(config_file, collection_interval, plugin_dir,
                      starttime, verbose, self_test,
                      logging.getLevelName(log_level))
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


@click.command()
@click.option('--collection-interval', default=30,
              help='Optional collection interval in seconds')
@click.option('--config-file', default=None,
              help='NuoCA configuration file')
@click.option('--plugin-dir', default=None,
              help='Optional path to plugin directory')
@click.option('--starttime', default=None,
              help='Optional start time in Epoch seconds '
                   'for first collection interval')
@click.option('--verbose', is_flag=True, default=False,
              help='Run with verbose messages written to stdout')
@click.option('--self-test', is_flag=True, default=False,
              help='Run 5 collection intervals then exit')
@click.option('--log-level', default='INFO',
              type=click.Choice(['CRITICAL', 'ERROR', 'WARNING',
                                 'INFO', 'DEBUG']),
              help='Set log level during test execution.')
def nuoca(config_file, collection_interval, plugin_dir,
          starttime, verbose, self_test, log_level):
  nuoca_run(config_file, collection_interval, plugin_dir,
          starttime, verbose, self_test, log_level)

if __name__ == "__main__":
  nuoca()

