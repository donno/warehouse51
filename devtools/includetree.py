"""Parses the /showincludes for the CL compiler and presents it as a tree.

This tool is for Microsoft Visual C++ compiler.
"""

from tkinter import *
from tkinter import ttk

import os.path


__version__ = '0.4.0'
__copyright__ = "Copyright 2014, https://github.com/donno/"


def process(path):
  """Process a file with the output of /showincludes.

  Expects lines to contain the string 'Note: including file: '.

  The depth/nesting is determined by the amount of whitespace after the prefix
  and the path.

  Provides an iterable of (depth, path) pairs.
  """
  def extract(lines):
    """Given a iterable of lines, extracts the useful information from it."""
    prefix = 'Note: including file: '
    for line in lines:
      if line.startswith(prefix):
        line = os.path.normpath(line[len(prefix):])
        # Determine the depth by counting the number of spaces starting the line.
        depth = len(line) - len(line.lstrip()) + 1
        yield (depth, line.strip())

  with open(path) as fr:
    lines = iter(fr)
    root = next(lines)
    yield (None, root.strip())
    for depth, path in extract(fr):
      yield (depth, path)


def insignificant(path):
  """Return True if path is considered insignificant."""

  # This part is simply an implementation detail for the code base that the
  # script was developed against. Ideally this would be moved out to a config
  # file.
  return path.endswith('Dll.H') or path.endswith('Forward.H') or \
    path.endswith('templates.H')


def select(app):
  #x, y = app.menu
  #print x, y
  #print app.tv.identify('item', x, y)
  item = app.tv.selection()[0]
  print(app.tv.item(item))
  print(item)


def show(path, options):
  """Shows the include tree for the given path using Tk.

  Support options:
    options.simple - simplify the include tree removing insignificant includes.
    options.common_path_prefix - a path that is common to a lot of paths that
                                 will be removed.
  """

  app = Tk()
  app.title('Include Tree')
  app.tv = ttk.Treeview(app)
  app.tv.pack(fill=BOTH, expand=1)

  menu = Menu(app, tearoff=0)
  menu.add_command(label="Select same", command=lambda app=app: select(app))

  def popup(event):
    app.menu = (event.x, event.y)
    menu.post(event.x_root, event.y_root)

  app.tv.bind("<Button-3>", popup)
  common_path_prefix = options.common_path_prefix.lower()

  tree = {}
  for depth, path in process(path):
    if common_path_prefix:
      if path[:len(common_path_prefix)].lower() == common_path_prefix:
        path = path[len(common_path_prefix):]

    if depth is None:
      item = app.tv.insert('', END, text=path)
      tree[1] = item
    elif depth:
      item = tree.get(depth)
      if not item:
        # Find the lowers item (maybe we skipped something because we filtered
        # it out.
        depth = max(tree.keys())
        item = tree.get(depth)

      item = app.tv.insert(tree[depth], END, text=path)
      tree[depth + 1] = item

  # Walk the tree looking for insignificant elements.
  #
  # An element is insignificant based on its name and typically refers to core
  # includes that aren't removable (for example, they exist to declare macros
  # for exporting/import a library as a DLL).
  items_to_remove = set()

  def find_insignificant_items(item):
    itemsToRemove = set()
    for child in app.tv.get_children(item):
      itemsToRemove.update(find_insignificant_items(child))

    path = app.tv.item(item)['text']
    if insignificant(path):
      itemsToRemove.add(item)
    return itemsToRemove

  if options.simple:
    for value in tree.values():
      items_to_remove.update(find_insignificant_items(value))

  app.tv.delete(*items_to_remove)

  app.mainloop()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser(description='Show an include tree.')
  parser.add_argument('path', metavar='PATH',
                      help='the path to the file containing the include tree')
  parser.add_argument('--simple', action='store_true',
                      help='simplify the include tree removing insignificant '
                           'includes.')
  parser.add_argument('--remove-prefix',
                      help='remove the following prefix from the start of '
                           'each path.',
                      dest='common_path_prefix',
                      default='')

  args = parser.parse_args()

  show(args.path, args)
