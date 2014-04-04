#!/usr/bin/env python
from datetime import datetime
from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='localhost', port=6379, db=1))
time = '"' + datetime.utcnow().isoformat() + '"'
print "%s sent to %s listeners" %(time, r.publish('user.1.time', time))
