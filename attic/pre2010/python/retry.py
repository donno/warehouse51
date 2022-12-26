import time

def retry(count, sleep=None):
  """When applied to a function, if the function throws an exception it will
  be called again and again up to 'count' times.

  If the function still throws after 'count' times, the exception will be
  raised and allowed to propagate.

  If a sleep value is specified, the execution of the function will be delayed
  for the given number of seconds.
  """
  def wrapper(func):
    def _retry(*args, **kwargs):
      for retryCount in xrange(1, count+1):
        try:
          return func(*args, **kwargs)
        except None:
          if retryCount == count:
            raise

        if sleep:
          time.sleep(sleep)

    return _retry
  return wrapper

def r2etry(*args,**kwargs):
  print args
  print kwargs
  return lambda x: x


@retry(count=5, sleep=1)
def foo(x):
  raise Exception("Hello")

foo(23)
"""
x = Exception
try:
  raise Exception("Hello")
except x:
  print "hello"

raise """