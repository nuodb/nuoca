import logging
import os
import re
import socket
import subprocess
import threading
from dateutil.parser import parse as date_parse
from calendar import timegm

from Queue import Queue, Empty

from nuoca_plugin import NuocaMPInputPlugin
from nuoca_util import nuoca_log
from pygrok import Grok

# NuoAdminAgentLog plugin
#
# Example NuoAdminAgentLog plugin configuration:
#
# - NuoAdminAgentLog:
#    description : Collection from NuoDB Admin logfile.
#    adminLogfile: full path to NuoDB Admin Logfile.


message_patterns = {
  # NuoAgent version: 3.0.master-3780
  "Environment.logEnv": [
    "NuoDB %{WORD:directory} directory: %{GREEDYDATA:value}",
    "NuoAgent version: %{GREEDYDATA:version}"],
  "LocalServer.logNewRole": "\[.*\] Converting to (?<action>LEADER) \(term=[0-9]+, index=[0-9]+\)( %{GREEDYDATA:comment})?",
  "PropertiesContainerImpl.logProps": "Property %{NOTSPACE:property}=%{GREEDYDATA:value}",
  "URLPropertiesProvider.<init>": ".*properties file: %{GREEDYDATA:propertyfile}",
  "PeerContainerImpl$LocalPeer.initStableId": "Initializing local peer.* uuid:%{UUID:stableid}",
  "PeerContainerImpl$LocalPeer.<init>": "local bind address=%{IPORHOST:bindhost}?/%{IPORHOST:bindaddr}?:%{POSINT:bindport}, hostname=%{IPORHOST:bhostname}",
  "PeerService$EntryListener.handleMessage": "Peering reply from \[%{IPORHOST:peerhost}?/%{IPORHOST:peeraddr}?:%{POSINT:peerport}, uuid:%{UUID:stableid}\] \(%{NUODB_AGENTTYPE:peertype}\)",
  "TagServer$DomainJoinedRunnable.run": "Region is: %{GREEDYDATA:region}",
  # INFO EventManager.notifyPeerEvent (serv-socket7-thread-62) Peer left: [Peer 10.3.91.5:48004 (broker)]
  "EventManager.notifyPeerEvent": "%{NUODB_ENTITY:entity} %{NUODB_ACTIONS:action}: \[%{NUODB_PEER:peer_description}\]",
  "EventManager.nofifyDomainEvent": "%{NUODB_ACTIONS:action} %{NUODB_ENTITY:entity}",

  # INFO    EventManager.notifyNodeEvent (serv-socket6-thread-163) Node joined: [Node SM db=[realtime] pid=17719 id=2 req=null (Peer 10.3.90.4:48004 (broker))]
  # WARNING EventManager.notifyNodeEvent (serv-socket7-thread-3222) Node joined with null Peer ignored: [Node SM db=[JPMC] pid=16015 id=11 req=SMs (10.3.91.4:48005)]
  "EventManager.notifyNodeEvent": "%{NUODB_ENTITY:entity} %{NUODB_ACTIONS:action}%{GREEDYDATA:comment}?: %{NUODB_NODE:node_description}",
  "EventManager.notifyNodeIdSet": "%{NUODB_ENTITY:entity} %{NUODB_ACTIONS:action}=%{POSINT:newnodeid} %{NUODB_NODE:node_description}",
  "EventManager.notifyNodeStateChange": "%{NUODB_ENTITY:entity} %{NUODB_ACTIONS:action} changed to %{WORD:node_state} %{NUODB_NODE:node_description}",
  "EventManager.notifyNodeFailure": [
    "%{NUODB_ENTITY:entity} %{NUODB_ACTIONS:action} peer=\[%{NUODB_PEER}\] startId=\[%{NUMBER:startId}\]:%{NUODB_GREEDYDATA:comment}",
    "%{NUODB_ENTITY:entity} %{NUODB_ACTIONS:action} %{NUODB_NODE:node_description}: %{NUODB_GREEDYDATA:comment}"],
  "ProcessService$ProcessReaper.reapConnected": "%{WORD:action} process with pid %{NUODB_PID:node_pid} and exit code %{NUMBER:exitcode}",
  "ProcessService.nodeLeft": [
    "%{WORD:action} up pid.%{NUMBER:node_pid} with exit code.%{NUMBER:exitcode}",
    "Marking process with %{NUODB_ENTITY:entity} object %{NUODB_NODE:node_description} for %{NUODB_ACTIONS:action}"],
  "NuoAgent.logReady": "%{GREEDYDATA:comment}; agent is ready",
  "NuoAgent.shutdown": "%{GREEDYDATA:comment}"

}

nuodb_patterns = {
  "NUODB_NODE": "\[Node %{WORD:node_type} db=\[%{WORD:dbname}\] pid=%{POSINT:node_pid} id=%{INT:nodeid} req=%{WORD:nodegroup} \((%{IPORHOST:peeraddr}:%{NUMBER:nodeport}|%{NUODB_PEER:peer_description})\)\]",
  "NUODB_ENTITY": "([nN]ode|[pP]eer|[dD]omain)",
  "NUODB_ACTIONS": "([Jj]oined|left|state|setId|failed|reaping)",
  "NUODB_AGENTTYPE": "(broker|agent)",
  "NUODB_PEER": "((Local)?Peer %{IPORHOST:peeraddr}:%{POSINT:peerport} \(%{NUODB_AGENTTYPE:peertype}\)|local)",
  "NUODB_PID": "[0-9]+(,[0-9]{3})?",
  # multi-line greedy
  "NUODB_GREEDYDATA": "(.*\n?)+"
}

# replace patterns with Grok
grok_patterns = {}
for logger, patterns in message_patterns.iteritems():
  if type(patterns) is not str:
    grok_patterns[logger] = [
      Grok("^%s" % (pattern), custom_patterns=nuodb_patterns) for pattern in
      patterns]
  else:
    grok_patterns[logger] = [
      Grok("^%s" % (patterns), custom_patterns=nuodb_patterns)]


def setregion(event):
  # do nothing for regions
  pass

def updatepeer(event):
  # do nothing for peers
  pass

def logevent(event):
  if 'logger' not in event:
    event['logger'] = None

def lifecycle(event):
  if event['action'] is not None:
    if event['entity'] == 'Node':
      if event['action'] == 'setId':
        event['node_state'] = "STARTED"
      elif event['action'] == 'joined':
        event['node_state'] = "STARTING"
      elif event['action'] == 'left':
        event['node_state'] = "EXITTED"
      elif event['action'] == 'failed':
        event['node_state'] = "FAILED"
      if 'observed' in event and event['observed'] is not None:
        event['action'] += "/" + event['observed']
  else:
    nuoca_log(logging.WARNING,
              "NuoAdminAgentLog plugin event without action: %8s %20s %s" % (
              event['loglevel'], event['logger'], event['message']))

def exitcycle(event):
  """
  %{WORD:op} up pid %{POSINT:pid} with exit code %{POSINT:exitcode}
  %{WORD:op} process with pid %{NUODB_PID:pid} and exit code %{POSINT:exitcode}
  """
  if 'action' in event:
    if 'exitcode' in event:
      event['comment'] = "exit code " + event['exitcode']
    event['entity'] = "Node"
    event['node_pid'] = event['node_pid'].replace(',', '')
    event['node_state'] = "FINISHED"
    lifecycle(event)


def checkproperty(event):
  # Do nothing for checkproperty
  pass

def mapstableid(event):
  # Do nothing for mapstableid
  pass

def peerhandle(event):
  if 'stableid' in event:
    event['iporaddr'] = event['peerhost']
    event['port'] = event['peerport']
    event['iporaddr'] = event['peeraddr']
    mapstableid(event)

def agentevent(event):
  if 'logger' in event:
    logger = event['logger']
    event['entity'] = "Peer"
    if logger.endswith('logReady'):
      event['node_state'] = "STARTED"
      event['action'] = 'State'
    elif logger.endswith('shutdown'):
      event['node_state'] = "EXITTED"
      event['action'] = 'Left'

def updateenv(event):
  if 'version' in event:
    event['entity'] = "Peer"
    event['action'] = 'Joined'
    event['node_state'] = "STARTING"
    event['comment'] = event['version']

def raftrole(event):
  event['entity'] = 'Peer'


event_handlers = {
  "PeerContainerImpl$LocalPeer": updatepeer,
  "Environment.logEnv": updateenv,
  "PropertiesContainerImpl.logProps": checkproperty,
  "TagServer$DomainJoinedRunnable.run": setregion,
  "ProcessService": exitcycle,
  "ProcessService$ProcessReaper": exitcycle,
  "EventManager": lifecycle,
  "PeerService$EntryListener.handleMessage": peerhandle,
  "NuoAgent": agentevent,
  # "LocalServer.logNewRole"                  : raftrole
}

def process(event):
  logevent(event)
  if 'logger' in event and event['logger'] is not None:
    elogger = event['logger']
    found = False
    if elogger in grok_patterns:
      patterns = grok_patterns[elogger]
      emsg = event['message']
      for grok in patterns:
        nevent = grok.match(emsg)
        if nevent:
          found = True
          event.update(nevent)
          break
      if not found:
        logging.debug("%s %s" % (elogger, emsg))
    if elogger in event_handlers:
      event_handlers[elogger](event)
    elif found:
      logger = elogger[:elogger.rfind('.')]
      if logger in event_handlers:
        event_handlers[logger](event)
    # print event


class Process:
  def __init__(self):
    grok_patterns = [
      "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:loglevel} %{NOTSPACE:logger} %{NOTSPACE:thread} +%{GREEDYDATA:message}",
      "%{TIMESTAMP_ISO8601:timestamp} \[%{POSINT:engine_pid}\] +%{GREEDYDATA:message}",
      "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:loglevel} +%{GREEDYDATA:message}"
    ]
    self.groks = [Grok(pattern) for pattern in grok_patterns]
    self.event = None
    self.processed_event = None

  def next(self, line):
    self.processed_event = None
    nevent = None
    for pattern in self.groks:
      nevent = pattern.match(line[:-1])
      if nevent:
        break
    if nevent is None and self.event is not None:
      self.event['message'] += '\n' + line[:-1]
    else:
      if self.event is not None:
        process(self.event)
        self.processed_event = self.event
        self.event = None
      if nevent is not None:
        self.event = nevent
    if not self.event:
      nuoca_log(logging.WARNING,
                "NuoAdminAgentLog plugin skipping line: %s" % line)
    pass

  def complete(self):
    self.processed_event = None
    if self.event is not None:
      process(self.event)
      self.processed_event = self.event


class MPNuoAdminAgentLog(NuocaMPInputPlugin):
  def __init__(self, parent_pipe):
    super(MPNuoAdminAgentLog, self).__init__(parent_pipe, 'NuoAdminAgentLog')
    self._config = None
    self._enabled = False
    self._agentLogfile = None
    self._tail_thread = None
    self._process_thread = None
    self._agentLogQueue = Queue()
    self._tail_subprocess = None
    self._line_counter = 0
    self._lines_processed = 0
    self._local_hostname = socket.gethostname()
    self._host_uuid_shortname = False
    self._host_shortid = None
    self._nuoAdminAgentLog_collect_queue = []

  @property
  def nuoAdminAgentLog_collect_queue(self):
    return self._nuoAdminAgentLog_collect_queue

  def _tail_forever_thread(self, filename):
    self._tail_subprocess = \
      subprocess.Popen(["tail", "-c", "+0", "-F", filename],
                        stdout=subprocess.PIPE)
    while self._enabled:
      line = self._tail_subprocess.stdout.readline()
      if line:
        self._line_counter += 1
        self._agentLogQueue.put(line)
    nuoca_log(logging.INFO,
              "NuoAdminAgentLog plugin tail_forever_thread "
              "completed %s lines" % str(self._line_counter))

  def _process_agent_log_thread(self):
    process = Process()
    line = None
    while self._enabled:
      try:
        line = self._agentLogQueue.get(block=True, timeout=10)
      except Empty:
        line = None
      if line:
        process.next(line)
        self._lines_processed += 1
      if process.processed_event:
        self.nuoAdminAgentLog_collect_queue.append(process.processed_event)
      if not line:
        process.complete()
        if process.processed_event:
          self.nuoAdminAgentLog_collect_queue.append(process.processed_event)
          process.event = None
          process.processed_event = None
    nuoca_log(logging.INFO,
              "NuoAdminAgentLog plugin process_agent_log_thread "
              "completed %s lines" % str(self._lines_processed))


  def startup(self, config=None):
    uuid_hostname_regex = \
      '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}-'
    try:
      self._config = config

      # Validate the configuration.
      required_config_items = ['agentLogfile']
      if not self.has_required_config_items(config, required_config_items):
        return False
      nuoca_log(logging.INFO, "NuoAdminAgentLog plugin config: %s" %
                str(self._config))

      # For Coach hostnames in the format: uuid-shortId
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']

      if self._host_uuid_shortname:
        m2 = re.search(uuid_hostname_regex, self._local_hostname)
        if m2:
          self._host_shortid = self._local_hostname[37:]

      self._agentLogfile = os.path.expandvars(config['agentLogfile'])
      self._enabled = True
      self._tail_thread = threading.Thread(target=self._tail_forever_thread,
                                      args=(self._agentLogfile,))
      self._tail_thread.daemon = True
      self._tail_thread.start()

      self._process_thread = \
        threading.Thread(target=self._process_agent_log_thread)
      self._process_thread.daemon = False
      self._process_thread.start()

      return True

    except Exception as e:
      nuoca_log(logging.ERROR, "NuoAdminAgentLog Plugin: %s" % str(e))
      return False

  def shutdown(self):
    self.enabled = False
    if self._tail_subprocess:
      self._tail_subprocess.terminate()
      self._tail_subprocess = None
    if self._process_thread:
      self._process_thread.join()

  def collect(self, collection_interval):
    rval = None
    try:
      nuoca_log(logging.DEBUG,
                "Called collect() in NuoAdminAgentLog Plugin process")
      base_values = super(MPNuoAdminAgentLog, self).\
        collect(collection_interval)
      base_values['Hostname'] = self._local_hostname
      if self._host_shortid:
        base_values['HostShortID'] = self._host_shortid
      rval = []
      collection_count = len(self._nuoAdminAgentLog_collect_queue)
      if not collection_count:
        return rval

      for i in range(collection_count):
        collected_dict = self._nuoAdminAgentLog_collect_queue.pop(0)
        collected_dict.update(base_values)
        if collected_dict['timestamp']:
          dt = date_parse(collected_dict['timestamp'])
          collected_dict['TimeStamp'] = timegm(dt.timetuple())
        rval.append(collected_dict)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
