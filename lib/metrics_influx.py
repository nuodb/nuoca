from contextlib import closing
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO

metrics = {}

def MONITOR_COUNT(k,values):
    raw = values[k]
    return "raw=%si" % (raw)

def MONITOR_DELTA(k,values):
    raw = int(values[k])
    rvalues="raw=%di" % (raw)
    if 'Milliseconds' in values:
        ms = int(values['Milliseconds'])
        rate = raw*1000./ms if ms != 0 else 0.
        rvalues += ",rate=%f" % (rate)
    return rvalues

def MONITOR_MILLISECONDS(k,values):
    raw = int(values[k])
    rvalues="raw=%di" % (raw)    
    if 'Milliseconds' in values:
        ms = int(values['Milliseconds'])
        value =  raw*1./ms if ms != 0 else 0.
        rvalues+= ",value=%f" % (value)
        if 'NumberCores' in values:
            ncores = int(values['NumberCores'])
            nvalue = value/ncores if ncores != 0 else 0.
            rvalues += ",normvalue=%f" % (nvalue)
                
    return rvalues

def MONITOR_NUMBER(k,values):
    raw = values[k]
    return "raw=%si" % (raw)

MONITOR_IDENTIFIER=None

def MONITOR_PERCENT(k,values):
    raw = values[k]
    rvalues = "raw=%si" % (raw)
    if 'NumberCores' in values:
        ncores = int(values['NumberCores'])
        if ncores != 0:
            value = int(raw)*1./ncores
            bycore= int(raw)*.01
            # norm   -> 0 <-> 100 * ncores
            # ncores -> 0 <-> ncores
            rvalues += ",norm=%f,ncores=%f" % (value,bycore)
            if k == 'PercentCpuTime':
                idle = 100*ncores - int(raw)
                # idle   -> 0 <-> 100 * ncores
                # nidle  -> 0 <-> ncores
                rvalues += ",idle=%di,nidle=%f" % (idle,float(idle)/ncores)
        else:
            # ncores only 0 at disconnect
            rvalues += ",norm=%f,ncores=%f" % (0.,0.)
            if k == 'PercentCpuTime':
                rvalues += ",idle=%di,nidle=%f" % (0.,0.)
    return rvalues

def summary(values):
    # from nuodbmgr
    def get(key):
        return int(values[key]) if key in values else 0

    activeTime = get("ActiveTime")
    deltaTime = get("Milliseconds")
    idleTime  = get("IdleTime")

    def v(raw):
        rvalues = "raw=%d" % (raw)
        if deltaTime > 0:
            rvalues += ",nthreads=%d" % (int(round(raw/deltaTime)))
            if activeTime > 0:
                multiplier = (deltaTime-idleTime)*1./deltaTime
                rvalues += ",percent=%d" % (int(round(multiplier*raw*100./activeTime)))
        return rvalues

    cpuTime   = get("UserMilliseconds") + get("KernelMilliseconds")
    syncTime  = get("SyncPointWaitTime") + get("StallPointWaitTime")
    syncTime -= get("PlatformObjectCheckOpenTime") + get("PlatformObjectCheckPopulatedTime") + get("PlatformObjectCheckCompleteTime")
    lockTime  = get("TransactionBlockedTime")
    fetchTime = get("PlatformObjectCheckOpenTime") + get("PlatformObjectCheckPopulatedTime") + get("PlatformObjectCheckCompleteTime") + get("LoadObjectTime")
    commitTime       = get("RemoteCommitTime")
    ntwkSendTime     = get("NodeSocketBufferWriteTime")
    archiveReadTime  = get("ArchiveReadTime")
    archiveWriteTime = get("ArchiveWriteTime") + get("ArchiveFsyncTime") + get("ArchiveDirectoryTime")
    journalWriteTime = get("JournalWriteTime") + get("JournalFsyncTime") + get("JournalDirectoryTime")
    throttleTime     = get("ArchiveSyncThrottleTime") + get("MemoryThrottleTime") + get("WriteThrottleTime")
    throttleTime    += get("ArchiveBandwidthThrottleTime") + get("JournalBandwidthThrottleTime")
    values = { 
        "Summary.Active" : v(activeTime),
        "Summary.CPU" : v(cpuTime),
        "Summary.Idle" : v(idleTime),
        "Summary.Sync" : v(syncTime),
        "Summary.Lock" : v(lockTime),
        "Summary.Fetch": v(fetchTime),
        "Summary.Commit": v(commitTime),
        "Summary.NtwkSend":v(ntwkSendTime),
        "Summary.ArchiveRead":v(archiveReadTime),
        "Summary.ArchiveWrite":v(archiveWriteTime),
        "Summary.JournalWrite":v(journalWriteTime),
        "Summary.Throttle":v(throttleTime)
    }
    return values


metrics = {
    "ActiveTime":                              MONITOR_MILLISECONDS,
    "ActualVersion":                           MONITOR_NUMBER,
    "AdminReceived":                           MONITOR_DELTA,
    "AdminSent":                               MONITOR_DELTA,
    "ArchiveBandwidthThrottleTime":            MONITOR_MILLISECONDS,
    "ArchiveBufferedBytes":                    MONITOR_DELTA,
    "ArchiveDirectory":                        MONITOR_IDENTIFIER,
    "ArchiveDirectoryTime":                    MONITOR_MILLISECONDS,
    "ArchiveFsyncTime":                        MONITOR_MILLISECONDS,
    "ArchiveQueue":                            MONITOR_COUNT,
    "ArchiveReadTime":                         MONITOR_MILLISECONDS,
    "ArchiveSyncThrottleTime":                 MONITOR_MILLISECONDS,
    "ArchiveWriteTime":                        MONITOR_MILLISECONDS,
    "AtomProcessingThreadBacklog":             MONITOR_MILLISECONDS,
    "BroadcastTime":                           MONITOR_MILLISECONDS,
    "BytesBuffered":                           MONITOR_DELTA,
    "BytesReceived":                           MONITOR_DELTA,
    "BytesSent":                               MONITOR_DELTA,
    "ChairmanMigration":                       MONITOR_DELTA,
    "CheckCompleteFull":                       MONITOR_DELTA,
    "CheckCompleteOptimized":                  MONITOR_DELTA,
    "ClientCncts":                             MONITOR_NUMBER,
    "ClientReceived":                          MONITOR_DELTA,
    "ClientSent":                              MONITOR_DELTA,
    "ClientThreadBacklog":                     MONITOR_MILLISECONDS,
    "Commits":                                 MONITOR_DELTA,
    "CreatePlatformRecordsTime":               MONITOR_MILLISECONDS,
    "CurrentActiveTransactions":               MONITOR_NUMBER,
    "CurrentCommittedTransactions":            MONITOR_NUMBER,
    "CurrentPurgedTransactions":               MONITOR_NUMBER,
    "CycleTime":                               MONITOR_MILLISECONDS,
    "Deletes":                                 MONITOR_DELTA,
    "DependentCommitWaits":                    MONITOR_NUMBER,
    "DiskWritten":                             MONITOR_DELTA,
    "EffectiveVersion":                        MONITOR_NUMBER,
    "HTTPProcessingThreadBacklog":             MONITOR_MILLISECONDS,
    "HeapActive":                              MONITOR_NUMBER,
    "HeapAllocated":                           MONITOR_NUMBER,
    "HeapMapped":                              MONITOR_NUMBER,
    "Hostname":                                MONITOR_IDENTIFIER,
    "IdManagerBlockingStallCount":             MONITOR_DELTA,
    "IdManagerNonBlockingStallCount":          MONITOR_DELTA,
    "IdleTime":                                MONITOR_MILLISECONDS,
    "Inserts":                                 MONITOR_DELTA,
    "JournalBandwidthThrottleTime":            MONITOR_MILLISECONDS,
    "JournalDirectoryTime":                    MONITOR_MILLISECONDS,
    "JournalFsyncTime":                        MONITOR_MILLISECONDS,
    "JournalQueue":                            MONITOR_COUNT,
    "JournalWriteTime":                        MONITOR_MILLISECONDS,
    "JrnlBytes":                               MONITOR_DELTA,
    "JrnlWrites":                              MONITOR_DELTA,
    "KernelMilliseconds":                      MONITOR_MILLISECONDS,
    "LoadObjectTime":                          MONITOR_MILLISECONDS,
    "LocalCommitOrderTime":                    MONITOR_MILLISECONDS,
    "LogMsgs":                                 MONITOR_COUNT,
    "Memory":                                  MONITOR_NUMBER,
    "MemoryThrottleTime":                      MONITOR_MILLISECONDS,
    "MessageSequencerMergeTime":               MONITOR_MILLISECONDS,
    "MessageSequencerSortTime":                MONITOR_MILLISECONDS,
    "MessagesReceived":                        MONITOR_DELTA,
    "MessagesSent":                            MONITOR_DELTA,
    "Milliseconds":                            MONITOR_MILLISECONDS,
    "NodeApplyPingTime":                       MONITOR_MILLISECONDS,
    "NodeId":                                  MONITOR_IDENTIFIER,
    "NodePingTime":                            MONITOR_MILLISECONDS,
    "NodePostMethodTime":                      MONITOR_MILLISECONDS,
    "NodeSocketBufferWriteTime":               MONITOR_MILLISECONDS,
    "NodeState":                               MONITOR_IDENTIFIER,
    "NodeType":                                MONITOR_IDENTIFIER,
    "NonChairSplitTime":                       MONITOR_MILLISECONDS,
    "NumSplits":                               MONITOR_DELTA,
    "NumberCores":                             MONITOR_NUMBER,
    "ObjectFootprint":                         MONITOR_NUMBER,
    "Objects"   :                              MONITOR_COUNT,
    "ObjectsBounced":                          MONITOR_DELTA,
    "ObjectsCreated":                          MONITOR_DELTA,
    "ObjectsDeleted":                          MONITOR_DELTA,
    "ObjectsDropped":                          MONITOR_DELTA,
    "ObjectsDroppedPurged":                    MONITOR_DELTA,
    "ObjectsExported":                         MONITOR_DELTA,
    "ObjectsImported":                         MONITOR_DELTA,
    "ObjectsLoaded":                           MONITOR_DELTA,
    "ObjectsPurged":                           MONITOR_DELTA,
    "ObjectsReloaded":                         MONITOR_DELTA,
    "ObjectsRequested":                        MONITOR_DELTA,
    "ObjectsSaved":                            MONITOR_DELTA,
    "OldestActiveTransaction":                 MONITOR_NUMBER,
    "OldestCommittedTransaction":              MONITOR_NUMBER,
    "PacketsReceived":                         MONITOR_DELTA,
    "PacketsSent":                             MONITOR_DELTA,
    "PageFaults":                              MONITOR_COUNT,
    "PendingEventsCommitTime":                 MONITOR_MILLISECONDS,
    "PendingInsertWaitTime":                   MONITOR_MILLISECONDS,
    "PendingUpdateStallCount":                 MONITOR_DELTA,
    "PendingUpdateWaitTime":                   MONITOR_MILLISECONDS,
    "PercentCpuTime":                          MONITOR_PERCENT,
    "PercentSystemTime":                       MONITOR_PERCENT,
    "PercentUserTime":                         MONITOR_PERCENT,
    "PlatformCatalogStallCount":               MONITOR_DELTA,
    "PlatformIndexCheckAcknowledgedTime":      MONITOR_MILLISECONDS,
    "PlatformObjectCheckCompleteTime":         MONITOR_MILLISECONDS,
    "PlatformObjectCheckOpenTime":             MONITOR_MILLISECONDS,
    "PlatformObjectCheckPopulatedTime":        MONITOR_MILLISECONDS,
    "ProcessId":                               MONITOR_IDENTIFIER,
    "PruneAtomsThrottleTime":                  MONITOR_MILLISECONDS,
    "PurgedObjects" :                          MONITOR_COUNT,
    "RefactorTXQueueTime":                     MONITOR_MILLISECONDS,
    "RemoteCommitTime":                        MONITOR_MILLISECONDS,
    "Rollbacks":                               MONITOR_DELTA,
    "SendQueueSize":                           MONITOR_NUMBER,
    "SendSortingQueueSize":                    MONITOR_NUMBER,
    "ServerReceived":                          MONITOR_DELTA,
    "ServerSent":                              MONITOR_DELTA,
    "SnapshotAlbumSize":                       MONITOR_NUMBER,
    "SnapshotAlbumTime":                       MONITOR_NUMBER,
    "SnapshotAlbumsClosed":                    MONITOR_DELTA,
    "SnapshotAlbumsClosedForGC":               MONITOR_DELTA,
    "SocketBufferBytes":                       MONITOR_NUMBER,
    "SqlListenerIdleTime":                     MONITOR_MILLISECONDS,
    "SqlListenerSqlProcTime":                  MONITOR_MILLISECONDS,
    "SqlListenerStallTime":                    MONITOR_MILLISECONDS,
    "SqlListenerThrottleTime":                 MONITOR_MILLISECONDS,
    "SqlMsgs":                                 MONITOR_DELTA,
    "StallPointWaitTime":                      MONITOR_MILLISECONDS,
    "Stalls":                                  MONITOR_DELTA,
    "SyncPointWaitTime":                       MONITOR_MILLISECONDS,
    "TransactionBlockedTime":                  MONITOR_MILLISECONDS,
    "Updates":                                 MONITOR_DELTA,
    "UserMilliseconds":                        MONITOR_MILLISECONDS,
    "WaitForSplitTime":                        MONITOR_MILLISECONDS,
    "WriteLoadLevel":                          MONITOR_NUMBER,
    "WriteThrottleSetting":                    MONITOR_NUMBER,
    "WriteThrottleTime":                       MONITOR_MILLISECONDS
}


def format(values):
    # metric,<identity tags> <fields> timestamp
    if 'TimeStamp' not in values:
        return
    
    timestamp = values['TimeStamp']
    # timestamp is in milliseconds -> nanoseconds
    timestamp = int(timestamp*1000000)
    nodetype  = values['NodeType']
    hostname  = values['Hostname']
    processid = values['ProcessId']
    nodeid    = values['NodeId']
    database  = values['Database']
    region    = "<unknown>"
    if 'Region' in values:
        region    = values['Region']


    header = ["TimeStamp","NodeType","Hostname","ProcessId","NodeId","Database","Region"]
    tags = "host=%s,nodetype=%s,pid=%s,nodeid=%s,db=%s,region=%s" % (hostname,nodetype,processid,nodeid,database,region)

    with closing(StringIO()) as buffer:
        for k in values:
            value_formatter = metrics[k] if k in metrics else None
            if value_formatter:
                rvalues = metrics[k](k,values)
                print >> buffer,"%s,%s %s %s" % (k,tags,rvalues,timestamp)
            elif k not in metrics and k not in header:
                # catch all if new metric added
                try:
                    rvalues = "raw=%di" % (int(values[k]))
                    print >> buffer,"%s,%s %s %s" % (k,tags,rvalues,timestamp)
                except:
                    pass
        summary_map = summary(values)
        for key,rvalues in summary_map.iteritems():
            print >> buffer,"%s,%s %s %s" % (key,tags,rvalues,timestamp)
        toinflux = buffer.getvalue()

    return ("text/plain; charset=us-ascii", toinflux)
