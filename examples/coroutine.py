def coroutine(f):
    """
    Start the coroutine automatically with the initial call to next()
    """
    def wrapped(*args, **kwargs):
        cor = f(*args, **kwargs)
        cor.next()
        return cor
    return wrapped
