


def union(this, that):
  """
    Returns the union of this and that.
  """
  assert isOverlapping(this, that)
  return (min(this.start, that.start), max(this.end, that.end))

class PairWrapper:
  def __init__(self, pair):
    self.start, self.end = pair

def isOverlapping(a, b):
  if a == b:
    return True

  if a.start < b.start:
    """
      a  |
      b         |
    """

    # Now if a.end is after b.start its overlapping.
    return a.end > b.start
  else:
    """
      a         |
      b  |
    """
    # If b.end > a.start its overlapping.
    return b.end > a.start


def reduce(items):
  """
    Given a list of items each with a start and end, returns a new list
    containing the set of items in that no item overlaps.

    Visual examples:
      |------------|   - a
          |-----|      - b

      In this case [a] would be returned.

      |------------|   - a
          |----------| - b

      In this case [(a.start, b.end)] would be returned.
  """

  newItems = []

  for item in items:
    a = PairWrapper(item)
    for index, existingItem in enumerate(newItems):
      b = PairWrapper(existingItem)
      if isOverlapping(a, b):
        newItems[index] = union(a, b)
        break
    else:
      newItems.append(item)

  return newItems


import unittest

class TestReduce(unittest.TestCase):
    #noOverlap = [(1, 4), (6, 7)]
    #equals    = [(1, 4), (1, 4)]

    def test_no_overlap(self):
      # The two items don't overlap.
      items = [(1, 4), (6, 7)]
      reducedItems = reduce(items)

      self.assertEqual(len(reducedItems), 2)

      for item in reducedItems:
        self.assertTrue(item in items)

    def test_equal(self):
      # The two items don't overlap.
      items = [(1, 4), (1, 4)]
      reducedItems = reduce(items)
      self.assertEqual(len(reducedItems), 1)
      self.assertEqual(reducedItems[0], items[0])

    def test_a_before_b_overlap(self):
      """
        a |----------|
        b    |------------|

      In this case [(a.start, b.end)] would be returned.
      """
      items = [(1, 5), (4, 8)]
      reducedItems = reduce(items)
      self.assertEqual(len(reducedItems), 1)
      self.assertEqual(reducedItems[0], (1, 8))

    def test_b_before_a_overlap(self):
      """
        a       |------------|
        b |----------|

      In this case [(b.start, a.end)] would be returned.
      """
      items = [(4, 8), (1, 5)]
      reducedItems = reduce(items)
      self.assertEqual(len(reducedItems), 1)
      self.assertEqual(reducedItems[0], (1, 8))

    def test_a_before_b_no_overlap(self):
      """
        a  |----|
        b         |----|
      """
      items = [(1, 2), (3, 4)]
      reducedItems = reduce(items)

      self.assertEqual(len(reducedItems), 2)
      for item in reducedItems:
        self.assertTrue(item in items)

    def test_b_before_a_no_overlap(self):
      """
        a         |----|
        b  |----|
      """
      items = [(3, 4), (1, 2)]
      reducedItems = reduce(items)

      self.assertEqual(len(reducedItems), 2)
      for item in reducedItems:
        self.assertTrue(item in items)

if __name__ == '__main__':
    unittest.main()
