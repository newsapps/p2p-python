import time
import p2p

def retry(ExceptionToCheck, tries=100, delay=4, backoff=2):
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
                except p2p.P2PException as e:
                    if int(e.args[1]["STATUS"]) == 403:
                        time.sleep(mdelay)
                        mtries -= 1
                        mdelay *= backoff
                    else:
		                return f(*args, **kwargs)
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry # true decorator
    return deco_retry
