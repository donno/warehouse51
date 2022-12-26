
# Possible features
# - http transport (tornado)
# - zeromq transport

class Protocol:
  def __init__(self):
    pass


class Task:
  def __init__(self, function, prerequisites=[]):
    self.function = function
    self.prerequisites = prerequisites
    self.complete = False

  def __call__(self):
    for prerequisite in self.prerequisites:
      assert prerequisite.complete

    result = self.function()
    self.complete = True
    return result

class TaskManager:
  def __init__(self):
    self.tasks = []
    
  def add(self, *tasks):
    for task in tasks:
      self.tasks.append(task)

  def run(self):
    # Find complete task
    
if __name__ == '__main__':

  def test():
    print "hello"


  # Three tasks
  # c depends on b which depends on a.

  a = Task(test)
  b = Task(test, [a])
  c = Task(test, [b])
  
  tm = TaskManager()
  tm.add(a, b, c)
  tm.run()

  c()
