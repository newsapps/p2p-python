# (almost) pure python
from copy import deepcopy
import utils


class BaseCache(object):
    """
    Base cache object for P2P. All P2P caching objects need to
    extend this class and implement its methods.
    """
    content_items_hits = 0
    content_items_gets = 0

    collections_hits = 0
    collections_gets = 0

    collection_layouts_hits = 0
    collection_layouts_gets = 0

    sections_hits = 0
    sections_gets = 0

    section_configs_hits = 0
    section_configs_gets = 0

    thumb_hits = 0
    thumb_gets = 0

    def __init__(self, prefix='p2p'):
        """
        Takes one parameter, the name of this cache
        """
        self.prefix = prefix

    def get_content_item(self, slug=None, id=None, query=None):
        self.content_items_gets += 1

        if slug:
            key = "_".join([self.prefix, 'content_item',
                            slug,
                            self.query_to_key(query)])
        elif id:
            key = "_".join([self.prefix, 'content_item',
                            str(id),
                            self.query_to_key(query)])
        else:
            raise TypeError("get_content_item() takes either a slug or "
                            "id keyword argument")
        ret = self.get(key)
        if ret:
            self.content_items_hits += 1
        return ret

    def save_content_item(self, content_item, query=None):
        key = "_".join([self.prefix, 'content_item',
                        content_item['slug'],
                        self.query_to_key(query)])
        self.set(key, content_item)

        key = "_".join([self.prefix, 'content_item',
                        str(content_item['id']),
                        self.query_to_key(query)])
        self.set(key, content_item)

    def get_thumb(self, slug):
        self.thumb_gets += 1

        key = "_".join([self.prefix, 'thumb', slug])
        ret = self.get(key)
        if ret:
            self.thumb_hits += 1
        return ret

    def save_thumb(self, thumb):
        key = "_".join([self.prefix, 'thumb', thumb['slug']])
        self.set(key, thumb)

    def get_collection(self, slug=None, id=None, query=None):
        self.collections_gets += 1

        if slug:
            key = "_".join([self.prefix, 'collection',
                            slug,
                            self.query_to_key(query)])
        elif id:
            key = "_".join([self.prefix, 'collection',
                            str(id), self.query_to_key(query)])
        else:
            raise TypeError("get_collection() takes either a slug or id keyword argument")
        ret = self.get(key)
        if ret:
            self.collections_hits += 1
        return ret

    def save_collection(self, collection, query=None):
        key = "_".join([self.prefix, 'collection',
                        collection['code'],
                        self.query_to_key(query)])
        self.set(key, collection)

        key = "_".join([self.prefix, 'collection',
                        str(collection['id']),
                        self.query_to_key(query)])
        self.set(key, collection)

    def get_collection_layout(self, slug, query=None):
        self.collection_layouts_gets += 1

        key = "_".join([self.prefix, 'collection_layout',
                        slug, self.query_to_key(query)])
        ret = self.get(key)
        if ret:
            ret['code'] = slug
            self.collection_layouts_hits += 1
        return ret

    def save_collection_layout(self, collection_layout, query=None):
        key = "_".join([self.prefix, 'collection_layout',
                       collection_layout['code'],
                       self.query_to_key(query)])
        self.set(key, collection_layout)

    def get_section(self, path):
        self.sections_gets += 1

        key = "_".join([self.prefix, 'section', path])

        ret = self.get(key)
        if ret:
            self.sections_hits += 1
        return ret

    def save_section(self, path, section):
        key = "_".join([self.prefix, 'section', path])
        self.set(key, section)

    def get_section_configs(self, path):
        self.section_configs_gets += 1

        key = "_".join([self.prefix, 'section_configs', path])

        ret = self.get(key)
        if ret:
            self.section_configs_hits += 1
        return ret

    def save_section_configs(self, path, section):
        key = "_".join([self.prefix, 'section_configs', path])
        self.set(key, section)

    def get_stats(self):
        return {
            "content_item_gets": self.content_items_gets,
            "content_item_hits": self.content_items_hits,
            "collections_gets": self.collections_gets,
            "collections_hits": self.collections_hits,
            "collection_layouts_gets": self.collection_layouts_gets,
            "collection_layouts_hits": self.collection_layouts_hits,
            "sections_gets": self.sections_gets,
            "sections_hits": self.sections_hits,
            "section_configs_gets": self.section_configs_gets,
            "section_configs_hits": self.section_configs_hits,
        }

    def get(self, key):
        raise NotImplementedError()

    def set(self, key, data):
        raise NotImplementedError()

    def clear(self):
        raise NotImplementedError()

    def query_to_key(self, query):
        if query is None:
            return ''

        return utils.dict_to_qs(query)


class DictionaryCache(BaseCache):
    """
    Cache object for P2P that stores stuff in dictionaries. Essentially
    a local memory cache.
    """
    cache = dict()

    def get(self, key):
        return deepcopy(self.cache[key]) if key in self.cache else None

    def set(self, key, data):
        self.cache[key] = deepcopy(data)

    def clear(self):
        self.cache = dict()


class NoCache(BaseCache):
    """
    Caching object for P2P that doesn't cache anything. For testing and
    development and such.
    """
    def get_content_item(self, slug=None, id=None, query=None):
        return None

    def save_content_item(self, content_item, query=None):
        pass

    def get_collection(self, slug=None, id=None, query=None):
        return None

    def save_collection(self, collection, query=None):
        pass

    def get_collection_layout(self, slug=None, id=None, query=None):
        return None

    def save_collection_layout(self, collection_layout, query=None):
        pass

    def get_section(self, path):
        return None

    def save_section(self, path, section):
        pass

    def get_section_configs(self, path):
        return None

    def save_section_configs(self, path, section):
        pass

    def get_thumb(self, slug):
        return None

    def save_thumb(self, thumb):
        pass


try:
    from django.core.cache import cache

    class DjangoCache(BaseCache):
        """
        Cache object for P2P that stores stuff using Django's cache API.
        """
        def get(self, key):
            return cache.get(key)

        def set(self, key, data):
            cache.set(key, data)

except ImportError, e:
    pass

try:
    import redis
    import pickle

    class RedisCache(BaseCache):
        """
        Cache object for P2P that stores stuff in Redis.
        """
        def __init__(self, prefix='p2p', host='localhost', port=6379, db=0):
            """
            Takes one parameter, the name of this cache
            """
            self.prefix = prefix
            self.r = redis.StrictRedis(host=host, port=port, db=db)

        def get(self, key):
            ret = self.r.get(key)
            return pickle.loads(ret) if ret else None

        def set(self, key, data):
            self.r.set(key, pickle.dumps(data))

        def clean(self):
            self.r.flushdb()

except ImportError, e:
    pass
