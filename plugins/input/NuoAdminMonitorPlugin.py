# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import logging
import os
import re
import requests
import threading

from pynuoca.nuoca_plugin import NuocaMPInputPlugin
from pynuoca.nuoca_util import nuoca_log, nuoca_gettimestamp, IntervalSync
from requests.auth import HTTPBasicAuth

# Unverified HTTPS request is being made because the NuoDB Admin service does
# not yet support service certificate verification.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# NuoAdminMonitor plugin
#
# Example NuoAdminMonitor plugin configuration for Legacy Admin Layer
#
# - NuoAdminMonitor:
#    description : Monitor NuoDB Admin layer
#    admin_host: localhost
#    admin_rest_api_port: 8888
#    domain_username: domain
#    domain_password: bird
#    admin_collect_interval: 10
#    admin_collect_timeout: 1
#
# Example NuoAdminMonitor plugin configuration for New Admin Layer
#
# - NuoAdminMonitor:
#    description : Monitor NuoDB Admin layer
#    nuocaCollectionName: NuoAdminMon2
#    api_server: localhost:8888
#    client_key: /opt/nuodb/tls-config/keys/nuocmd.pem
#    server_cert: None
#    admin_collect_interval: 10
#    admin_collect_timeout: 1


class NuoAdminMonitorPlugin(NuocaMPInputPlugin):

  # NOTE: member variables that start with "_legacyAdmin_" refer to
  # the legacy Admin layer.  Member variables that start with
  # "_newAdmin_" refer to New (version 3.3) Admin layer

  DEFAULT_API_SERVER = 'localhost:8888'

  def __init__(self, parent_pipe):
    super(NuoAdminMonitorPlugin, self).__init__(parent_pipe, 'NuoAdminMon')
    self._config = None
    self._enabled = False
    self._database_regex_pattern = '.*'
    self._is_legacyAdmin = None
    self._nuocaCollectionName = 'NuoAdminMon'  # default

    #
    # Legacy Admin
    self._legacyAdmin_host = None
    self._legacyAdmin_rest_api_port = 8888
    self._legacyAdmin_auth = None
    self._legacyAdmin_base_url = None
    #
    # API endpoints:
    self._legacyAdmin_domain_enforcer_url = None
    #
    # self._numon_handler_ready = False
    self._legacyAdmin_domain_username = 'domain'
    self._legacyAdmin_domain_password = 'bird'
    self._domain_metrics = None
    self._host_uuid_shortname = False
    self._timer_thrd = None
    #
    # Variables commmon to _legacyAdmin_ and _new_
    self._admin_collect_interval = 10
    self._admin_collect_timeout = 1
    self._admin_collect_sync = None
    self._monitor_collect_queue = []
    #
    # New Admin
    self._newAdmin_api_server = NuoAdminMonitorPlugin.DEFAULT_API_SERVER
    self._newAdmin_client_key = None
    self._newAdmin_server_cert = None
    self._newAdmin_base_url = None
    self._newAdmin_requests_server_verify = False

    self._newAdmin_regions_url = None
    self._newAdmin_archives_url = None
    self._newAdmin_databases_url = None
    self._newAdmin_kvstore_url = None
    self._newAdmin_peers_url = None
    self._newAdmin_processes_url = None

  def _get_newAdmin_url(self):
    base_url = self._newAdmin_api_server
    if (not base_url.startswith('http://') and
          not base_url.startswith('https://')):  # noqa
      if self._newAdmin_client_key is None and \
              self._newAdmin_server_cert is None:
        base_url = 'http://' + base_url
      else:
        base_url = 'https://' + base_url
    return base_url

  @property
  def monitor_collect_queue(self):
    return self._monitor_collect_queue

  def get_legacyAdmin_rest_url(self, rest_url):
    try:
      req = requests.get(rest_url, auth=self._legacyAdmin_auth,
                         timeout=self._admin_collect_timeout)
      if req.status_code != 200:
        err_msg = "NuoAdminMon: Error code '%d' when " \
                  "calling Admin Rest API: %s" \
                  % (req.status_code, rest_url)
        nuoca_log(logging.ERROR, err_msg)
        return {'nuoca_collection_error': err_msg}
      return req.json()
    except requests.RequestException as e:
      err_msg = str(e)
      nuoca_log(logging.ERROR, err_msg)
      return {'nuoca_collection_error': err_msg}
    except Exception as e:
      err_msg = str(e)
      nuoca_log(logging.ERROR, err_msg)
      return {'nuoca_collection_error': err_msg}

  def get_newAdmin_rest_url(self, rest_url):
    get_data = True
    rval = {'data': []}
    offset = 0
    limit = 20
    try:
      while get_data:
        rest_url_page = "%s?offset=%d&limit=%d" % (rest_url, offset, limit)
        req = requests.get(rest_url_page, cert=self._newAdmin_client_key,
                           verify=self._newAdmin_requests_server_verify,
                           timeout=self._admin_collect_timeout)
        if req.status_code != 200:
          err_msg = "NuoAdminMon: Error code '%d' when " \
                    "calling Admin Rest API: %s" \
                    % (req.status_code, rest_url)
          nuoca_log(logging.ERROR, err_msg)
          return {'nuoca_collection_error': err_msg}
        req_response = req.json()
        if 'hasNext' in req_response and req_response['hasNext']:
          get_data = True
          offset += limit
        else:
          get_data = False
        if 'data' in req_response:
          for item in req_response['data']:
            rval['data'].append(item)
        else:
          rval['data'].append(req_response)

      return rval
    except requests.RequestException as e:
      err_msg = str(e)
      nuoca_log(logging.ERROR, err_msg)
      return {'nuoca_collection_error': err_msg}
    except Exception as e:
      err_msg = str(e)
      nuoca_log(logging.ERROR, err_msg)
      return {'nuoca_collection_error': err_msg}

  def get_legacyAdmin_enforcer(self):
    return self.get_legacyAdmin_rest_url(self._legacyAdmin_domain_enforcer_url)

  def get_legacyAdmin_regions(self):
    return self.get_legacyAdmin_rest_url(self._newAdmin_regions_url)

  def get_newAdmin_regions(self):
    return self.get_newAdmin_rest_url(self._newAdmin_regions_url)

  def get_newAdmin_archives(self):
    return self.get_newAdmin_rest_url(self._newAdmin_archives_url)

  def get_newAdmin_databases(self):
    return self.get_newAdmin_rest_url(self._newAdmin_databases_url)

  def get_newAdmin_database(self, dbname):
    db_url = '%s/%s' % (self._newAdmin_databases_url, dbname)
    return self.get_newAdmin_rest_url(db_url)

  def get_newAdmin_kvstore(self):
    return self.get_newAdmin_rest_url(self._newAdmin_kvstore_url)

  def get_newAdmin_peers(self):
    return self.get_newAdmin_rest_url(self._newAdmin_peers_url)

  def get_newAdmin_processes(self):
    return self.get_newAdmin_rest_url(self._newAdmin_processes_url)

  def _legacyAdmin_collector_thread(self, collect_timestamp):
    region_result_desired_fields = [u'region']
    host_result_desired_fields = \
      [u'stableId', u'hostname', u'port', u'version', u'address',
       u'isBroker', u'ipaddress', u'id']
    host_tags_desired_fields = \
      [u'default_archive_base', u'journal_base', u'archive_base',
       u'default_region', u'region', u'os_num_cpu', u'cores', u'os_num_cores',
       u'default_journal_base', u'ostype', u'cputype', u'os_ram_mb',
       u'osversion', u'os_num_fs']
    processes_desired_fields = \
      [u'status', u'uid', u'hostname', u'pid', u'nodeId', u'port',
       u'version', u'address', u'agentid', u'type', u'dbname']
    databases_desired_fields = \
    [u'status', u'name', u'tagConstraints', u'variables', u'groupOptions',
     u'archivesByGroup', u'archives', u'template', u'active',
     u'unmet_messages', u'options', u'ismet']
    database_boolean_fields = \
    [u'active', u'ismet']

    collect_timestamp = nuoca_gettimestamp() * 1000

    # print "\n\nCollection Timestamp: %s" % collect_timestamp
    enforcer_result = self.get_legacyAdmin_enforcer()
    # print "Result from Rest API %s: %s" % (self._domain_enforcer_url, enforcer_result)
    if 'nuoca_collection_error' in enforcer_result:
      base_collection = {"TimeStamp": collect_timestamp,
                         'nuoca_collection_error': enforcer_result[
                           'nuoca_collection_error']}
      self._monitor_collect_queue.append(base_collection)
    regions_result = self.get_legacyAdmin_regions()
    # print "Result from Rest API %s: %s" % (self._regions_url, regions_result)
    if 'nuoca_collection_error' in regions_result:
      base_collection = {"TimeStamp": collect_timestamp,
                         'nuoca_collection_error': regions_result[
                           'nuoca_collection_error']}
      self._monitor_collect_queue.append(base_collection)
    else:
      region_count = 0
      for region in regions_result:
        base_collection = {"TimeStamp": collect_timestamp,
                           u'domainEnforcerEnabled': enforcer_result[
                             u'domainEnforcerEnabled']}
        for region_field in region_result_desired_fields:
          base_collection[region_field] = \
            regions_result[region_count][region_field]
        for host in region['hosts']:
          for host_field in host_result_desired_fields:
            base_collection["admin.%s" % host_field] = host[host_field]
          for host_tag_field in host_tags_desired_fields:
            base_collection["tag.%s" % host_tag_field] = \
              host['tags'][host_tag_field]
          for process in host['processes']:
            process_collection = {}
            for process_field in processes_desired_fields:
              process_collection["process.%s" % process_field] \
                = process[process_field]
            process_collection.update(base_collection)
            self._monitor_collect_queue.append(process_collection)
        for database in region['databases']:
          database_collection = {}
          for database_field in databases_desired_fields:
            if database_field in database_boolean_fields:
              database_collection["database.%s" % database_field] = \
                str(database[database_field]).lower()
            else:
              database_collection["database.%s" % database_field] = \
                str(database[database_field])
          database_collection.update(base_collection)
          self._monitor_collect_queue.append(database_collection)
        region_count += 1

  def _newAdmin_collector_thread(self, collect_timestamp):
    # Skipped collection of storage groups, kvstore.
    region_desired_fields = [u'id', u'name']
    archive_desired_fields = \
      [u'host', u'state', u'id', u'path', u'dbName']
    database_desired_fields = \
      [u'state', u'incarnation', u'name',
       u'hostAssignments', u'name', u'servers',
       u'databaseOptions', u'defaultRegionId']
    peers_desired_fields = \
      [u'connectedState', u'peerMemberState', u'isLocal',
       u'address', u'peerState', u'id']
    process_desired_fields = \
      [u'labels', u'pid', u'lastHeardFrom', u'port', u'regionName',
       u'hostname', u'nodeId', u'isExternalStartup', u'state', u'version',
       u'archiveId', u'type', u'regionId', u'host', u'address', u'startId',
       u'archiveDir', u'dbName', u'durableState', u'ipAddress']
    collect_timestamp = nuoca_gettimestamp() * 1000

    # Peers
    local_nuoadmin_id = None
    peers_result = self.get_newAdmin_peers()
    if not peers_result or 'data' not in peers_result:
      base_collection = {"TimeStamp": collect_timestamp,
                         'nuoca_collection_error':
                           "Unable to get peers information"}
      self._monitor_collect_queue.append(base_collection)
      return
    if 'nuoca_collection_error' in peers_result:
      base_collection = {"TimeStamp": collect_timestamp,
                         'nuoca_collection_error': peers_result[
                           'nuoca_collection_error']}
      self._monitor_collect_queue.append(base_collection)
      return
    # print "Result from Rest API %s: %s" % (self._peers_url, peers_result)
    for peer in peers_result['data']:
      if bool(peer['isLocal']):
        local_nuoadmin_id = peer['id']
    for peer in peers_result['data']:
      base_collection = {"TimeStamp": collect_timestamp,
                         'NuoCA.docType': 'peer',
                         'NuoCA.ApiServerID': local_nuoadmin_id}
      peer_collection = {}
      for peer_field in peers_desired_fields:
        collection_fieldname = '%s.%s' % (base_collection['NuoCA.docType'],
                                          peer_field)
        base_collection[collection_fieldname] = str(peer[peer_field])
      peer_collection.update(base_collection)
      self._monitor_collect_queue.append(peer_collection)

    # Regions
    regions_result = self.get_newAdmin_regions()
    # print "Result from Rest API %s: %s" % (self._regions_url, regions_result)
    for region in regions_result['data']:
      base_collection = {"TimeStamp": collect_timestamp,
                         'NuoCA.docType': 'region',
                         'NuoCA.ApiServerID': local_nuoadmin_id}
      region_collection = {}
      for region_field in region_desired_fields:
        collection_fieldname = '%s.%s' % (base_collection['NuoCA.docType'],
                                          region_field)
        base_collection[collection_fieldname] = str(region[region_field])
      region_collection.update(base_collection)
      self._monitor_collect_queue.append(region_collection)

    # Archives
    archives_result = self.get_newAdmin_archives()
    # print "Result from Rest API %s: %s" % (self._archives_url, archives_result)
    for archive in archives_result['data']:
      base_collection = {"TimeStamp": collect_timestamp,
                         'NuoCA.docType': 'archive',
                         'NuoCA.ApiServerID': local_nuoadmin_id}
      archive_collection = {}
      for archive_field in archive_desired_fields:
        collection_fieldname = '%s.%s' % (base_collection['NuoCA.docType'],
                                          archive_field)
        base_collection[collection_fieldname] = str(archive[archive_field])
      archive_collection.update(base_collection)
      self._monitor_collect_queue.append(archive_collection)

    # Databases
    databases_result = self.get_newAdmin_databases()
    # print "Result from Rest API %s: %s" % (self._databases_url, databases_result)
    if 'data' in databases_result:
      for db_item in databases_result['data']:
        base_collection = {"TimeStamp": collect_timestamp,
                           'NuoCA.docType': 'database',
                           'NuoCA.ApiServerID': local_nuoadmin_id}
        dbname = db_item['name']
        database_result = self.get_newAdmin_database(dbname)
        # print "Result from Rest API %s/%s: %s" % (self._databases_url,
        #                                          dbname, database_result)
        for database in database_result['data']:
          database_collection = {}
          for database_field in database_desired_fields:
            collection_fieldname = '%s.%s' % (base_collection['NuoCA.docType'],
                                              database_field)
            database_collection[collection_fieldname] = \
              str(database[database_field])
          # Deal with 'regions' like this
          collection_fieldname = '%s.%s' % (base_collection['NuoCA.docType'],
                                            'regions')
          database_collection[collection_fieldname] = \
            str(database['regions'].keys())
          database_collection.update(base_collection)
          self._monitor_collect_queue.append(database_collection)

    # Processes
    processes_result = self.get_newAdmin_processes()
    # print "Result from Rest API %s: %s" % (self._processes_url, processes_result)
    if 'data' in processes_result:
      for process in processes_result['data']:
        base_collection = {"TimeStamp": collect_timestamp,
                           'NuoCA.docType': 'process',
                           'NuoCA.ApiServerID': local_nuoadmin_id}
        process_results = {}
        for process_field in process_desired_fields:
          if process_field in process:
            collection_fieldname = '%s.%s' % (base_collection['NuoCA.docType'],
                                              process_field)
            process_results[collection_fieldname] = str(process[process_field])
        # Deal with 'options' like this
        for options_field in process['options']:
          collection_fieldname = '%s.%s.%s' % \
                                 (base_collection['NuoCA.docType'],
                                  'options', options_field)
          process_results[collection_fieldname] = \
            str(process['options'][options_field])
        process_results.update(base_collection)
        self._monitor_collect_queue.append(process_results)

  def _legacyAdmin_timer_thread(self):
    while self._enabled:
      collect_timestamp = self._admin_collect_sync.wait_for_next_interval()
      collect_thread = threading.Thread(
        target=self._legacyAdmin_collector_thread,
        args=(collect_timestamp,))
      collect_thread.daemon = True
      collect_thread.start()

  def _newAdmin_timer_thread(self):
    while self._enabled:
      collect_timestamp = self._admin_collect_sync.wait_for_next_interval()
      collect_thread = threading.Thread(target=self._newAdmin_collector_thread,
                                        args=(collect_timestamp,))
      collect_thread.daemon = True
      collect_thread.start()

  def startup(self, config=None):
    try:
      self._config = config
      if not config:
        nuoca_log(logging.ERROR, "NuoAdminMon plugin: missing config file.")
        return False

      # Validate the configuration.
      #required_config_items = ['admin_host']
      #if not self.has_required_config_items(config, required_config_items):
      #  return False

      # Don't reveal the domain password in the NuoCA log file.
      display_config = {}
      display_config.update(config)
      display_config['domain_password'] = ''
      nuoca_log(logging.INFO, "NuoAdminMonitor plugin config: %s" %
                str(display_config))

      if 'nuocaCollectionName' in config:
        self._nuocaCollectionName = config['nuocaCollectionName']

      # Legacy Admin
      if 'admin_host' in config:
        self._legacyAdmin_host = os.path.expandvars(config['admin_host'])
        if self._legacyAdmin_host:
          self._is_legacyAdmin = True
      if 'domain_username' in config:
        self._legacyAdmin_domain_username = \
          os.path.expandvars(config['domain_username'])
      if 'domain_password' in config:
        self._legacyAdmin_domain_password = \
          os.path.expandvars(config['domain_password'])
      if 'admin_rest_api_port' in config:
        if isinstance(config['admin_rest_api_port'], int):
          self._legacyAdmin_rest_api_port = config['admin_rest_api_port']
        else:
          self._legacyAdmin_rest_api_port = int(os.path.expandvars(
              config['admin_rest_api_port']))

      # New Admin
      if 'api_server' in config:
        self._newAdmin_api_server = os.path.expandvars(config['api_server'])
        self._is_legacyAdmin = False
      if 'client_key' in config:
        self._newAdmin_client_key = os.path.expandvars(config['client_key'])
      if 'server_cert' in config:
        self._newAdmin_server_cert = os.path.expandvars(config['server_cert'])

      if not self._legacyAdmin_host and not self._newAdmin_api_server:
        err_msg = "Config must have 'admin_host' for legacy Admin, " \
                  "or 'api_server' for new Admin"
        nuoca_log(logging.ERROR, "NuoAdminMonitor Plugin: %s" % err_msg)
        return False

      if 'admin_collect_interval' in config:
        if isinstance(config['admin_collect_interval'], int):
          self._admin_collect_interval = config['admin_collect_interval']
        else:
          self._admin_collect_interval = \
            os.path.expandvars(config['admin_collect_interval'])
      if 'admin_collect_timeout' in config:
        if isinstance(config['admin_collect_timeout'], int):
          self._admin_collect_timeout = config['admin_collect_timeout']
        else:
          self._admin_collect_timeout = \
            os.path.expandvars(config['admin_collect_timeout'])
      if 'database_regex_pattern' in config:
        self._database_regex_pattern = config['database_regex_pattern']
      if 'host_uuid_shortname' in config:
        self._host_uuid_shortname = config['host_uuid_shortname']

      if self._is_legacyAdmin:
        self._legacyAdmin_base_url = "http://%s:%d/api/2" % \
                                     (self._legacyAdmin_host,
                                      self._legacyAdmin_rest_api_port)
        self._legacyAdmin_domain_enforcer_url = "%s/domain/enforcer" % \
                                                self._legacyAdmin_base_url
        self._newAdmin_regions_url = "%s/regions" % self._legacyAdmin_base_url
        self._legacyAdmin_auth = \
          HTTPBasicAuth(self._legacyAdmin_domain_username,
                        self._legacyAdmin_domain_password)
        nuoca_start_ts = None
        if 'nuoca_start_ts' in config:
          nuoca_start_ts = config['nuoca_start_ts']
        self._admin_collect_sync = IntervalSync(self._admin_collect_interval,
                                                seed_ts=nuoca_start_ts)

        self._enabled = True
        self._timer_thrd = \
          threading.Thread(target=self._legacyAdmin_timer_thread)
        self._timer_thrd.daemon = True
        self._timer_thrd.start()
      else:
        admin_url = self._get_newAdmin_url()
        self._newAdmin_base_url = "%s/api/1" % admin_url
        self._newAdmin_regions_url = "%s/regions" % self._newAdmin_base_url
        self._newAdmin_archives_url = "%s/archives" % self._newAdmin_base_url
        self._newAdmin_databases_url = "%s/databases" % self._newAdmin_base_url
        self._newAdmin_kvstore_url = "%s/kvstore" % self._newAdmin_base_url
        self._newAdmin_peers_url = "%s/peers" % self._newAdmin_base_url
        self._newAdmin_processes_url = "%s/processes" % self._newAdmin_base_url

        nuoca_start_ts = None
        if 'nuoca_start_ts' in config:
          nuoca_start_ts = config['nuoca_start_ts']
        self._admin_collect_sync = IntervalSync(self._admin_collect_interval,
                                                seed_ts=nuoca_start_ts)

        self._enabled = True
        self._timer_thrd = threading.Thread(target=self._newAdmin_timer_thread)
        self._timer_thrd.daemon = True
        self._timer_thrd.start()

      return True
    except Exception as e:
      nuoca_log(logging.ERROR, "NuoAdminMonitor Plugin: %s" % str(e))
      return False

  def shutdown(self):
    self.enabled = False
    pass

  def collect(self, collection_interval):
    rval = None
    try:
      nuoca_log(logging.DEBUG, "Called collect() in NuoAdminMonitor Plugin process")
      base_values = super(NuoAdminMonitorPlugin, self).collect(collection_interval)
      collection_count = len(self.monitor_collect_queue)
      if not collection_count:
        return rval

      rval = []
      for i in range(collection_count):
        collected_dict = self.monitor_collect_queue.pop(0)
        if self._nuocaCollectionName:
          collected_dict['nuocaCollectionName'] = self._nuocaCollectionName
        if 'process.dbname' in collected_dict:
          m = re.search(self._database_regex_pattern, collected_dict['process.dbname'])
          if m:
            rval.append(collected_dict)
        else:
          rval.append(collected_dict)
    except Exception as e:
      nuoca_log(logging.ERROR, str(e))
    return rval
