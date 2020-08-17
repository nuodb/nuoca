# (C) Copyright NuoDB, Inc. 2017-2020
#
# This source code is licensed under the MIT license found in the LICENSE
# file in the root directory of this source tree.

from nuomon_monitor import MetricsListener, EventListener
from nuomon_util import *
from pubsub import pub
import threading

from pynuoca.nuoca_util import nuoca_log

__all__ = ['MetricsConsumer', 'MetricsProducer', 'EventConsumer', 'EventProducer']


class AtomicCounter:
    """An atomic, thread-safe incrementing counter."""

    def __init__(self, initial=0):
        """Initialize a new atomic counter to given initial value (default 0)."""
        self.value = initial
        self._lock = threading.Lock()

    def increment(self, num=1):
        """Atomically increment the counter by num (default 1) and return the new value. """
        with self._lock:
            self.value += num
            return self.value


# Need request/reply for current state.
class EventConsumer(object):
    id_generator = AtomicCounter(0)

    def __init__(self, **args):
        for k, v in args.iteritems():
            setattr(self, k, v)
        replyToId = str(EventConsumer.id_generator.increment())
        self.__replyChannel = 'event.request.%s' % (replyToId)

    def __request_latest(self):
        pub.subscribe(self._onEvent, self.__replyChannel)
        pub.sendMessage('event.sync.request', replyTo=self.__replyChannel)
        pub.unsubscribe(self._onEvent, self.__replyChannel)

    def request_domain_state(self):
        self.__request_latest()

    @print_exc
    def start(self):
        # request full set of data to send then subscribe for data stream.
        self.__request_latest()
        pub.subscribe(self._onEvent, 'event.queue')

    @print_exc
    def stop(self):
        print '%s.stop' % (self.__class__.__name__)
        pub.unsubscribe(self._onEvent, 'event.queue')

    def onEvent(self, event, entity_type, entity_data, event_data):
        pass

    def _onEvent(self, event, entity_type, entity_data, event_data):
        self.onEvent(event, entity_type, entity_data, event_data)


class MetricsConsumer(object):
    """
    baseclass to listen to and request metric events
    Two types of events:
    -  description - describes each metric
    -  values      - update values or latest values (on update)
    """
    id_generator = AtomicCounter(0)

    def __init__(self, **args):
        """ args (that this class will look at)
            mode :  "full", "changed"
            filter : <callable>(identity)
        """
        for k, v in args.iteritems():
            setattr(self, k, v)
        self.mode = getattr(self, 'mode', 'full')
        self.filter = getattr(self, 'filter', lambda x: True)

        self.replyToId = str(MetricsConsumer.id_generator.increment())
        self.replyMetricsChannel = 'metrics.requested.description.%s' % (self.replyToId)
        self.replyValuesChannel = 'metrics.requested.values.%s' % (self.replyToId)
        pass

    def __del__(self):
        pass

    @property
    def instanceId(self):
        return self.replyToId

    def onMetrics(self, description):
        pass

    def onValues(self, values):
        pass

    def __request_latest(self):
        pub.subscribe(self._onMetrics, self.replyMetricsChannel)
        pub.subscribe(self._onValues, self.replyValuesChannel)
        pub.sendMessage('metrics.request.description', replyTo=self.replyMetricsChannel)
        pub.sendMessage('metrics.request.values', replyTo=self.replyValuesChannel)
        pub.unsubscribe(self._onMetrics, self.replyMetricsChannel)
        pub.unsubscribe(self._onValues, self.replyValuesChannel)

    def request_metrics(self):
        self.__request_latest()

    @print_exc
    def start(self):
        # request full set of data to send then subscribe for data stream.
        self.__request_latest()
        if self.mode == 'full':
            pub.subscribe(self._onValues, 'metrics.values.full')
        else:
            pub.subscribe(self._onValues, 'metrics.values.updated')

    @print_exc
    def stop(self):
        print '%s.stop' % (self.__class__.__name__)
        if self.mode == 'full':
            pub.unsubscribe(self._onValues, 'metrics.values.full')
        else:
            pub.unsubscribe(self._onValues, 'metrics.values.updated')
        pub.subscribe(self._onShutdown, self.replyValuesChannel)
        pub.sendMessage('metrics.request.values', replyTo=self.replyValuesChannel)
        pub.unsubscribe(self._onShutdown, self.replyValuesChannel)

    def _filter(self, identity):
        return self.filter(identity)
        # filter = getattr(self,'filter',None)
        # return filter is None or filter(identity)

    @print_exc
    @trace
    def _onMetrics(self, description):
        self.onMetrics(description)
        pass

    @print_exc
    @trace
    def _onValues(self, identity, body):
        # publish 'full' latest values, 'changed' modified values
        if self._filter(identity):
            body.update(identity.toValues())
            self.onValues(body)

    @print_exc
    @trace
    def _onShutdown(self, identity, body):
        """ publish one more set of values - all zeros """
        print '%s._onShutdown' % (self.__class__.__name__)
        if not self._filter(identity):
            return
        if self.mode != 'full':
            # changed mode we only want to publish values != 0
            removekeys = [k for k, v in body.iteritems() if v == 0]
            for k in removekeys:
                del body[k]
        zerokeys = [k for k, v in body.iteritems() if v != 0 and type(v) is int]
        for k in zerokeys:
            body[k] = 0
        body.update(identity.toValues())
        print '%s._onShutdown: %s' % (self.__class__.__name__, body)
        self.onValues(body)


class EventProducer(EventListener):
    def __init__(self):
        super(EventListener, self).__init__()
        self.cache = {EventListener.EntityType.PEER: [],
                      EventListener.EntityType.PROCESS: [],
                      EventListener.EntityType.DATABASE: []
                      }
        pub.subscribe(self.onEventRequest, 'event.sync.request')

    def onEvent(self, event, entity_type, entity_data, event_data):
        if entity_type in self.cache:
            if event == EventListener.EventType.JOINED:
                cached = self.cache[entity_type]
                cached.append(entity_data)
            elif event == EventListener.EventType.LEFT:
                cached = self.cache[entity_type]
                for obj, ndx in enumerate(cached):
                    if obj == entity_data:
                        del obj[ndx]
                        break
        pub.sendMessage('event.queue', event=event, entity_type=entity_type, entity_data=entity_data,
                        event_data=event_data)
        pass

    def onEventRequest(self, replyTo):
        peers = self.cache[EventListener.EntityType.PEER]
        for edata in peers:
            pub.sendMessage(replyTo, event=EventListener.EventType.JOINED, entity_type=EventListener.EntityType.PEER,
                            entity_data=edata, event_data=None)
        dbs = self.cache[EventListener.EntityType.DATABASE]
        for edata in dbs:
            pub.sendMessage(replyTo, event=EventListener.EventType.JOINED,
                            entity_type=EventListener.EntityType.DATABASE,
                            entity_data=edata, event_data=None)
        processes = self.cache[EventListener.EntityType.PROCESS]
        for edata in processes:
            pub.sendMessage(replyTo, event=EventListener.EventType.JOINED, entity_type=EventListener.EntityType.PROCESS,
                            entity_data=edata, event_data=None)


class MetricsProducer(MetricsListener):
    def __init__(self):
        super(MetricsProducer, self).__init__()
        nuoca_log(logging.DEBUG, "nuomon_broadcast MetricsProducer.__init__()")
        self.identity = None

    @print_exc
    def onStart(self, metrics):
        super(MetricsProducer, self).onStart(metrics)
        nuoca_log(logging.DEBUG, "nuomon_broadcast MetricsProducer.onStart()")
        pub.sendMessage('metrics.description', description=self.metrics)
        pub.subscribe(self.onMetricsRequest, 'metrics.request.description')
        pub.subscribe(self.onValuesRequest, 'metrics.request.values')

    @print_exc
    def onChange(self, values):
        nuoca_log(logging.DEBUG, "nuomon_broadcast MetricsProducer.onChange()")
        if len(self.values) > 0:
            pub.sendMessage('metrics.values.updated', identity=self.getIdentity(), body=values)
        super(MetricsProducer, self).onChange(values)
        pub.sendMessage('metrics.values.full', identity=self.getIdentity(), body=self.values)

    @print_exc
    @trace
    def onMetricsRequest(self, replyTo):
        pub.sendMessage(replyTo, description=self.metrics)

    @print_exc
    @trace
    def onValuesRequest(self, replyTo):
        if self.identity:
            pub.sendMessage(replyTo, identity=self.identity, body=self.values)

    def getIdentity(self):
        class Identity(object):
            def __init__(self, **kwds):
                self.__dict__ = kwds

            def toValues(self):
                return dict(Database=self.database,
                            NodeId=self.nodeid,
                            Hostname=self.hostname,
                            ProcessId=self.processid,
                            NodeType=self.nodetype)

        if self.identity is None:
            values = self.values
            self.identity = Identity(database=values['Database'],
                                     nodeid=values['NodeId'],
                                     hostname=values['Hostname'],
                                     processid=values['ProcessId'],
                                     nodetype=values['NodeType'])
        return self.identity


if __name__ == "__main__":
    from nuomon_monitor import get_nuodb_metrics
    import time, traceback, yaml, sys


    class Handle(MetricsConsumer):
        """ example handler that listens for messages from BradcastListener."""

        def __init__(self):
            super(Handle, self).__init__()
            pass

        def onMetrics(self, description):
            print yaml.dump(description)
            pass

        def onValues(self, values):
            print yaml.dump(values)
            pass


    broker = 'localhost'
    d = get_nuodb_metrics(broker, 'bird', listener=MetricsProducer)

    # request / reply assumes that data has already been cached.
    time.sleep(2)
    obj = Handle()

    print 'start...'
    obj.start()
    time.sleep(1)
    d.disconnect()
    # d.wait_forever()
