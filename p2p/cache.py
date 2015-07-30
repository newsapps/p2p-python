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

        if slug is None and id is None:
            raise TypeError("get_content_item() takes either a slug or "
                            "id keyword argument")

        if id:
            lookup_key = self.make_key('content_item', str(id), 'lookup')
            slug = self.get(lookup_key)
            if slug is None:
                return None

        key = self.make_key('content_item', slug, self.query_to_key(query))
        ret = self.get(key)
        if ret:
            self.content_items_hits += 1
        return ret

    def save_content_item(self, content_item, query=None):
        # save the actual data
        key = self.make_key(
            'content_item', content_item['slug'], self.query_to_key(query))
        self.set(key, content_item)

        # save a reference. Since we might need to lookup by id,
        # we'll save a simple item that tells us the slug for that id
        lookup_key = self.make_key(
            'content_item', str(content_item['id']), 'lookup')
        self.set(lookup_key, content_item['slug'])

        # Log our query
        self.log_key('content_item', content_item['slug'], query)

    def remove_content_item(self, slug=None, id=None):
        raise NotImplementedError

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

    def get_collection(self, slug, query=None):
        self.collections_gets += 1

        key = self.make_key('collection', slug, self.query_to_key(query))
        ret = self.get(key)
        if ret:
            self.collections_hits += 1
        return ret

    def save_collection(self, collection, query=None):
        key = self.make_key(
            'collection', collection['code'], self.query_to_key(query))
        self.set(key, collection)

        # Log our query
        self.log_key('collection', collection['code'], query)

    def remove_collection(self, slug):
        raise NotImplementedError

    def get_collection_layout(self, slug, query=None):
        self.collection_layouts_gets += 1

        key = self.make_key(
            'collection_layout', slug, self.query_to_key(query))
        ret = self.get(key)
        if ret:
            ret['code'] = slug
            self.collection_layouts_hits += 1
        return ret

    def save_collection_layout(self, collection_layout, query=None):
        key = self.make_key('collection_layout',
                            collection_layout['code'],
                            self.query_to_key(query))
        self.set(key, collection_layout)

        # Log our query
        self.log_key('collection_layout', collection_layout['code'], query)

    def remove_collection_layout(self, code):
        return NotImplementedError

    def get_section(self, path, query=None):
        self.sections_gets += 1

        key = self.make_key('section', path, self.query_to_key(query))

        ret = self.get(key)
        if ret:
            self.sections_hits += 1
        return ret

    def save_section(self, path, section, query=None):
        key = self.make_key('section', path, self.query_to_key(query))
        self.log_key('section', path, query)
        self.set(key, section)

        # Log our query
        self.log_key('section', path, query)

    def remove_section(self, path):
        raise NotImplementedError

    def get_section_configs(self, path, query=None):
        self.section_configs_gets += 1

        key = self.make_key('section_configs', path, self.query_to_key(query))

        ret = self.get(key)
        if ret:
            self.section_configs_hits += 1
        return ret

    def save_section_configs(self, path, section, query=None):
        key = self.make_key('section_configs', path, self.query_to_key(query))
        self.log_key('section_configs', path, query)
        self.set(key, section)

        # Log our query
        self.log_key('section_configs', path, query)

    def remove_section_configs(self, path):
        raise NotImplementedError

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
        """
        Get data from a cache key
        """
        raise NotImplementedError()

    def set(self, key, data):
        """
        Save data to a cache key
        """
        raise NotImplementedError()

    def log_key(self, type, id, query):
        """
        Log the different components of the keys that are so that we can
        discover what kinds of query responses we're currently caching.
        Requires a structured data store, like redis or an RDBMS.
        """
        raise NotImplementedError()

    def log_ls(self, type, id=None):
        """
        List item ids or item queries that are cached.
        """
        raise NotImplementedError()

    def log_remove(self, type, id, query):
        """
        Remove something from the key log
        """
        raise NotImplementedError()

    def clear(self):
        """
        Clear the entire cache
        """
        raise NotImplementedError()

    def query_to_key(self, query):
        """
        Take a query in the form of a dictionary and turn it into something
        that can be used in a cache key
        """
        if query is None:
            return ''

        return utils.dict_to_qs(query)

    def make_key(self, *args):
        """
        Take any number of arguments and return a key string
        """
        return ':'.join([self.prefix] + list(args))


class DictionaryCache(BaseCache):
    """
    Cache object for P2P that stores stuff in dictionaries. Essentially
    a local memory cache.
    """
    cache = dict()
    log = dict()

    def get(self, key):
        return deepcopy(self.cache[key]) if key in self.cache else None

    def set(self, key, data):
        self.cache[key] = deepcopy(data)

    def log_key(self, type, id, query):
        if type not in self.log:
            self.log[type] = set()
        self.log[type].add(id)

        keyname = self.make_key(type, id)
        if keyname not in self.log:
            self.log[keyname] = dict()
        self.log[keyname][utils.dict_to_qs(query)] = deepcopy(query)

    def log_ls(self, type, id=None):
        if id is None:
            return self.log[type].copy() if type in self.log else None
        else:
            keyname = self.make_key(type, id)
            return self.log[keyname].values() if keyname in self.log else None

    def log_remove(self, type, id, query):
        if type in self.log:
            if id in self.log[type]:
                self.log[type].remove(id)
            if len(self.log[type]) == 0:
                del self.log[type]

        keyname = self.make_key(type, id)
        query_str = utils.dict_to_qs(query)
        if keyname in self.log:
            if query_str in self.log[keyname]:
                del self.log[keyname][query_str]
            if len(self.log[keyname]) == 0:
                del self.log[keyname]

    def clear(self):
        self.cache.clear()
        self.log.clear()


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

    def get_section(self, path, query=None):
        return None

    def save_section(self, path, section, query=None):
        pass

    def get_section_configs(self, path, query=None):
        return None

    def save_section_configs(self, path, section, query=None):
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

        def log_key(self, type, id, query):
            pass

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

        def remove_content_item(self, slug=None, id=None):
            """
            Remove all instances of this content item from the cache
            """
            # make sure we have arguments
            if slug is None and id is None:
                raise TypeError("remove_content_item() takes either a slug or "
                                "id keyword argument")

            # If we got an id, we need to lookup the slug
            if id:
                lookup_key = self.make_key('content_item', str(id), 'lookup')
                slug = self.get(lookup_key)
                # Couldn't find the slug so bail
                if slug is None:
                    return False

            # use the log to find all the queries used, construct a list
            # of cache keys to delete
            queries = self.log_ls('content_item', slug)
            matching_keys = [
                self.make_key(
                    'content_item', slug,
                    self.query_to_key(q)) for q in queries
            ]

            # if we don't have any keys, bail
            if not matching_keys:
                return False

            if id is None:
                # we need to grab a copy of the content item in order to
                # retrieve the id. We need the id to remove the lookup key.
                content_item = self.get(matching_keys[0])
                # key is not used
                if content_item is None:
                    return False
                id = content_item['id']
                lookup_key = self.make_key('content_item', str(id), 'lookup')

            # add the lookup key to our list of keys, then delete them all
            matching_keys.append(lookup_key)
            self.r.delete(*matching_keys)
            return True

        def remove_collection(self, slug):
            """
            Remove all instances of this collection from the cache
            """
            # use the log to find all the queries used, construct a list
            # of cache keys to delete
            queries = self.log_ls('collection', slug)
            matching_keys = [
                self.make_key(
                    'collection', slug, self.query_to_key(q)) for q in queries
            ]

            # if we don't have any keys, bail
            if not matching_keys:
                return False

            # add the lookup key to our list of keys, then delete them all
            self.r.delete(*matching_keys)
            return True

        def remove_collection_layout(self, slug):
            """
            Remove all instances of this collection layout from the cache
            """
            # use the log to find all the queries used, construct a list
            # of cache keys to delete
            queries = self.log_ls('collection_layout', slug)
            matching_keys = [
                self.make_key('collection_layout',
                              slug, self.query_to_key(q)) for q in queries
            ]

            # if we don't have any keys, bail
            if not matching_keys:
                return False

            # add the lookup key to our list of keys, then delete them all
            self.r.delete(*matching_keys)
            return True

        def remove_section(self, path):
            """
            Remove all instances of this section from the cache
            """
            # use the log to find all the queries used, construct a list
            # of cache keys to delete
            queries = self.log_ls('section', path)
            matching_keys = [
                self.make_key('section',
                              path, self.query_to_key(q)) for q in queries
            ]

            # if we don't have any keys, bail
            if not matching_keys:
                return False

            # add the lookup key to our list of keys, then delete them all
            self.r.delete(*matching_keys)
            return True

        def remove_section_configs(self, path):
            """
            Remove all instances of the configs for this section from the cache
            """
            # use the log to find all the queries used, construct a list
            # of cache keys to delete
            queries = self.log_ls('section_configs', path)
            matching_keys = [
                self.make_key('section_configs',
                              path, self.query_to_key(q)) for q in queries
            ]

            # if we don't have any keys, bail
            if not matching_keys:
                return False

            # add the lookup key to our list of keys, then delete them all
            self.r.delete(*matching_keys)
            return True

        def get(self, key):
            ret = self.r.get(key)
            return pickle.loads(ret) if ret else None

        def set(self, key, data):
            self.r.set(key, pickle.dumps(data))

        def log_key(self, type, id, query):
            self.r.sadd(
                self.make_key(type),
                id)
            self.r.sadd(
                self.make_key(type, id),
                pickle.dumps(query))

        def log_ls(self, type, id=None):
            if id is None:
                key = self.make_key(type)
            else:
                key = self.make_key(type, id)

            while True:
                query = self.r.spop(key)
                if query:
                    yield pickle.loads(query)
                else:
                    break

        def log_remove(self, type, id, query):
            self.r.srem(
                self.make_key(type), id)
            self.r.srem(
                self.make_key(type, id),
                pickle.dumps(query))

        def clear(self):
            self.r.flushdb()

except ImportError, e:
    pass
