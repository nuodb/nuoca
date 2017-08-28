from wrapt import decorator
import traceback,logging

@decorator
def print_exc(wrapped, instance, args, kwargs):
    try:
        return wrapped(*args, **kwargs)
    except Exception as e:
        print str(e)
        traceback.print_exc()

@decorator
def trace(wrapped,instance,args,kwargs):
    """ work on this """
    logging.getLogger('trace').info("%s" % (wrapped.__qualname__ if hasattr(wrapped,'__qualname__') else wrapped.__name__))
    return wrapped(*args,**kwargs)
        
