from requests.adapters import HTTPAdapter, DEFAULT_POOLBLOCK
from requests.packages.urllib3.poolmanager import PoolManager


class TribAdapter(HTTPAdapter):
    def init_poolmanager(self, connections, maxsize, block=DEFAULT_POOLBLOCK):
        self._pool_connections = connections
        self._pool_maxsize = maxsize
        self._pool_block = block

        self.poolmanager = PoolManager(num_pools=connections, maxsize=maxsize,
                                       block=block,
                                       ssl_version='TLSv1')
