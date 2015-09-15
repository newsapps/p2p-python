import time
import logging
logger = logging.getLogger(__name__)


def retry(ExceptionToCheck, tries=100, delay=4, backoff=3):
    """
    Retry decorator
    original from http://wiki.python.org/moin/PythonDecoratorLibrary#Retry
    """
    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck:
                    logger.debug("Error. Retrying in %s" % mdelay)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                logger.debug("Error. Final try in %s" % mdelay)
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry
