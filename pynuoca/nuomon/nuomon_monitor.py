#!/usr/bin/python

# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

import os, sys, yaml
import time, aenum
import socket
import threading, logging
from nuomon_util import *

from pynuodb.session import Session, BaseListener, SessionMonitor
from pynuodb.entity import Domain
from xml.etree import ElementTree

# base class, do not override methods

__all__ = ['MetricsListener', 'EventListener', 'get_nuodb_metrics']


class BaseMetricsListener(BaseListener):
    def __init__(self):
        super(BaseMetricsListener, self).__init__()
        self.__first = True
        self.__process = None

    @property
    def process(self):
        return self.__process

    @process.setter
    def process(self, p):
        self.__process = p

    def __get_item(self, attrs):
        units = ["COUNT", "MILLISECONDS", "STATE",
                 "NUMBER", "PERCENT", "IDENTIFIER",
                 "DELTA"]
        return {"unit": units[int(attrs['units']) - 1],
                "description": attrs['header']}

    # @trace
    def message_received(self, root):
        def parseStr(x):
            try:
                return int(x)
            except:
                return x

        items = {}
        if root.tag == "Items":
            for child in root:
                items[child.attrib['name']] = self.__get_item(child.attrib)
            items['Database'] = dict(unit="IDENTIFIER", description="Database Name")
            items['Region'] = dict(unit="IDENTIFIER", description="Region Name")
            items['DomainName'] = dict(unit="IDENTIFIER", description="Domain Name")
            items['Version'] = dict(unit="IDENTIFIER", description="NuoDB Version String")
            self.onStart(items)
        elif root.tag == 'Status':
            values = dict([(k, parseStr(v)) for k, v in root.attrib.iteritems()])
            if self.__first:
                values['Database'] = self.process.database.name
                values['Region'] = self.process.peer.get_tag('region')
                values['DomainName'] = self.process.peer.domain.domain_name
                values['Version'] = self.process.version
                self.__first = False
            values['TimeStamp'] = int(time.time() * 1000.0)
            self.onChange(values)

    def closed(self):
        self.onEnd()
        pass


# interface, do override
# onEvent
class EventListener(object):
    class EventType(int, aenum.Enum):
        JOINED = 1
        LEFT = -1
        CHANGED = 0
        FAILED = -2

    class EntityType(str, aenum.Enum):
        DATABASE = 'database'
        PEER = 'peer'
        PROCESS = 'process'

    def __init__(self):
        pass

    def onEvent(self, event, entity_type, entity_data, event_data):
        #        print 'onEvent',event, entity_type, entity_data
        #        if event_data is None:
        #            print event_data
        #        else:
        #            print event_data
        pass


# interface, do override
#   onStart
#   onStat
#   onEnd


class MetricsListener(BaseMetricsListener):
    """ Base class for metrics collection.
    Remembers previous values"""

    def __init__(self):
        super(MetricsListener, self).__init__()
        self.__metrics = {}
        self.__values = {}
        pass

    @property
    def metrics(self):
        return self.__metrics

    @property
    def values(self):
        return self.__values

    def init(self, args):
        return self

    def onStart(self, metrics):
        """ remembers metrics  """
        self.__metrics = metrics

    def onChange(self, metrics):
        """ remembers previous values """
        self.__values.update(metrics)

    def onEnd(self):
        """ zero all values """
        zeroMetrics = {}
        for k, v in self.__values.iteritems():
            if v != 0 and type(v) is int:
                zeroMetrics[k] = 0
        zeroMetrics['TimeStamp'] = int(time.time() * 1000.0)
        self.onChange(zeroMetrics)
        pass


class MetricsDomain(Domain):
    def __init__(self, broker, user, password, listener):
        Domain.__init__(self, broker, user, password, listener)

    def wait_forever(self, log=False):
        try:
            while True:
                time.sleep(10)
        except:
            pass
        finally:
            self.disconnect()
            if log:
                print "disconnect..."


# @print_exc
def get_nuodb_metrics(broker, password, listener, user='domain', database=None, host=None, process=None, args=None,
                      domain_listener=None):
    # Listener is class derived from MetricsListener
    if listener is None:
        listener = MetricsListener
    if domain_listener is None:
        domain_listener = EventListener

    domain = DomainListener(user=user,
                            password=password,
                            database=database,
                            host=host,
                            process=process,
                            listener=listener,
                            args=args,
                            domain_listener=domain_listener())
    return MetricsDomain(broker, user, password, domain)


# implementation
""" TODO:  Add event stream """


class DomainListener(object):
    cached_addresses = {}
    running_monitors = {}

    def __init__(self, **kwds):
        for k, v in kwds.iteritems():
            setattr(self, k, v)
        self.listener = getattr(self, 'listener', MetricsListener)
        self.domain_listener = getattr(self, 'domain_listener', EventListener())

    def __monitoring_peer(self, peer):
        """ apply filters if specified """
        return True

    def peer_joined(self, peer):
        # apply filters if specified
        if not self.__monitoring_peer(peer):
            return
        id = dict(hostname=peer.hostname,
                  address=peer.address,
                  port=peer.port,
                  # is_broker= peer.broker,
                  # agent_id=  peer.agent_id,
                  version=peer.version)
        self.domain_listener.onEvent(EventListener.EventType.JOINED,
                                     EventListener.EntityType.PEER,
                                     id, None)

    def peer_left(self, peer):
        # apply filters if specified
        if not self.__monitoring_peer(peer):
            return
        id = dict(hostname=peer.hostname,
                  address=peer.address,
                  port=peer.port,
                  # is_broker= peer.broker,
                  # agent_id=  peer.agent_id,
                  version=peer.version)
        self.domain_listener.onEvent(EventListener.EventType.LEFT,
                                     EventListener.EntityType.PEER,
                                     id, None)

    def process_joined(self, p):
        logging.debug("process joined: %s" % str(p))
        db = p.database
        # apply filters if specified
        if self.database and self.database != db.name:
            return
        if self.host:
            addresses = [p.hostname, p.peer.address, p.peer.hostname,
                         self.getaddr(p.hostname),
                         self.getaddr(p.peer.address),
                         self.getaddr(p.peer.hostname)]
            if self.host not in addresses:
                return
        if self.process and self.database and self.process != p.node_id:
            return
        if self.process and self.host and self.process != p.pid:
            return

        # setup monitors
        id = dict(hostname=p.hostname,
                  dbname=p.database.name,
                  port=p.port,
                  pid=p.pid,
                  # is_transaction = p.transactional,
                  version=p.version,
                  node_id=p.node_id)
        self.domain_listener.onEvent(EventListener.EventType.JOINED,
                                     EventListener.EntityType.PROCESS,
                                     id, None)
        self.monitorEngine(p)

    def process_left(self, p):
        logging.debug("process left: %s" % str(p))
        if str(p) in self.running_monitors:
            id = dict(hostname=p.hostname,
                      dbname=p.database.name,
                      port=p.port,
                      pid=p.pid,
                      # is_transaction = p.transactional,
                      version=p.version,
                      node_id=p.node_id)
            self.domain_listener.onEvent(EventListener.EventType.LEFT,
                                         EventListener.EntityType.PROCESS,
                                         id, None)
            monitor = self.running_monitors[str(p)]
            del self.running_monitors[str(p)]

    def process_failed(self, peer, reason):
        print 'failed: ', peer
        id = dict(hostname=peer.hostname,
                  address=peer.address,
                  port=peer.port,
                  # is_broker= peer.broker,
                  # agent_id=  peer.agent_id,
                  version=peer.version)
        self.domain_listener.onEvent(EventListener.EventType.FAILED,
                                     EventListener.EntityType.PROCESS,
                                     id, reason)
        pass

    def process_status_changed(self, p, status):
        id = dict(hostname=p.hostname,
                  dbname=p.database.name,
                  port=p.port,
                  pid=p.pid,
                  # is_transaction = p.transactional,
                  version=p.version,
                  node_id=p.node_id)
        self.domain_listener.onEvent(EventListener.EventType.CHANGED,
                                     EventListener.EntityType.PROCESS,
                                     id, status)

    def database_joined(self, database):
        id = dict(database=database.name)
        self.domain_listener.onEvent(EventListener.EventType.JOINED,
                                     EventListener.EntityType.DATABASE,
                                     id, None)
        pass

    def database_left(self, database):
        id = dict(database=database.name)
        self.domain_listener.onEvent(EventListener.EventType.LEFT,
                                     EventListener.EntityType.DATABASE,
                                     id, None)
        pass

    def getaddr(self, hostname):
        try:
            if hostname not in self.cache_addresses:
                self.cache_addressed[hostname] = socket.gethostbyname(hostname)
        except:
            self.cached_addresses[hostname] = None
        return self.cached_addresses[hostname]

    @print_exc
    def monitorEngine(self, process):
        """ Monitor statistics from a TE or SM """

        # attach and monitor stats from engine
        engine_key = self.__get_engine_key(process)
        engine_session = Session(process.address, port=process.port, service="Monitor")
        engine_session.authorize("Cloud", engine_key)

        args = getattr(self, 'args', None)
        if args is None:
            callbk = self.listener()
        else:
            callbk = self.listener().init(args)
        callbk.process = process
        monitor = SessionMonitor(engine_session, listener=callbk)
        monitor.start()
        engine_session.doConnect()
        self.running_monitors[str(process)] = monitor

    @print_exc
    def getSyncTrace(self, process):
        # attach and monitor stats from engine
        engine_key = self.__get_engine_key(process)
        engine_session = Session(process.address, port=process.port, service="Monitor")
        engine_session.authorize("Cloud", engine_key)

    def closed(self):
        for name, monitor in self.running_monitors.iteritems():
            monitor.close()
        self.running_monitors = {}

    def __get_engine_key(self, process):
        session = Session(process.peer.connect_str, service="Manager")
        session.authorize(self.user, self.password)
        pwd_response = session.doRequest(attributes={"Type": "GetDatabaseCredentials",
                                                     "Database": process.database.name})
        pwd_xml = ElementTree.fromstring(pwd_response)
        pwd = pwd_xml.find("Password").text.strip()
        return pwd

    def waitForTerminate(self):
        while len(self.running_monitors):
            threading.Thread.join(self.running_monitors.values()[0])


if __name__ == "__main__":
    import optparse

    parser = optparse.OptionParser(usage="%prog [options] [hostname:port]",
                                   description="""Attaches
                                   to nodes and recieves stat data on a periodic basis.  You can
                                   filter which processes to attach to.  For a single process specify via
                                   a given host and pid or database and nodeid.  For all processes on a
                                   host specify the host.  For all processes of a given database specify
                                   the database.
                                   """)
    parser.add_option("-u", "--user", dest="user", default="domain", help="Domain user (domain).")
    parser.add_option("-p", "--password", dest="password", default="bird", help="Domain password (bird).")
    parser.add_option("-d", "--database", dest="database", default=None, help="Monitor given database.")
    parser.add_option("-n", "--host", dest="host", default=None, help="Only monitor process on this host.")
    parser.add_option("-i", "--process", dest="process", default=None, type='int',
                      help="Process identifier, pid (with host) or nodeId (with datbase).")
    parser.add_option("-m", "--mode", dest="mode", choices=['full', 'changed'], default='changed',
                      help="Controls output.")
    (options, args) = parser.parse_args()

    # validate input 
    if options.process and options.database and options.host:
        parser.print_help()
        sys.exit(1)
    if options.process and not (options.database or options.host):
        parser.print_help()
        sys.exit(1)

    broker = "localhost"
    if len(args) == 1:
        broker = args[0]
    elif len(args) > 1:
        parser.print_help()
        sys.exit(1)


    class DemoListener(MetricsListener):
        DOHEADER = True

        def __init__(self):
            super(DemoListener, self).__init__()
            self.mode = 'full'

        def init(self, args):
            if 'mode' in args:
                self.mode = args['mode']
            return self

        def onStart(self, metrics):
            super(DemoListener, self).onStart(metrics)
            if DemoListener.DOHEADER:
                DemoListener.DOHEADER = False
                print "Description of metrics..."
                for k, v in self.desciption.iteritems():
                    print "%-48s: %s" % ("%s(%s)" % (k, v['unit']), v['description'])
                print

        @print_exc
        def onChange(self, values):
            super(DemoListener, self).onChange(values)
            if self.mode == 'full':
                use = self.values
            else:
                use = values
            header = "%s" % (self.process)
            display = {header: use}
            print yaml.dump(display, default_flow_style=False)

        def onEnd(self):
            super(DemoListener, self).onEnd()
            print "Goodbye from: %s:%s %s(%s)" % (
            self.values['Hostname'], self.values['ProcessId'], self.values['Database'], self.values['NodeId'])
            pass


    args = {'mode': options.mode}
    del options.mode
    d = get_nuodb_metrics(broker=broker, listener=DemoListener, args=args, **options.__dict__)
    d.wait_forever()
