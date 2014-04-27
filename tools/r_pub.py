from redis import Redis, ConnectionPool
r = Redis(connection_pool=ConnectionPool(host='localhost', port=6379, db=1))

n = 0
def out(n):
    print r.publish('user.1.worlds', n)
    return n + 1