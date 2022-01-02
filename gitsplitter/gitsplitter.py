"""gitsplitter

Splits individual commits or groups of commits into separate branches.

It takes a list of commits and breaks them out into separate branches, by
creating new branches and cherry-picking certain commits into each branch.
"""

def handle(newBranch, sourceBranch, commits):
  """Create a new branch in a git repository called `newBranch` branched off of
  `sourceBranch` and cherry-pick each commit in `commits` into it.
  """

  print 'git checkout -b %s %s' % (newBranch, sourceBranch)
  for commit in commits:
    print 'git cherry-pick %s' % (commit)


def input(line):
  """Parse a line of input to determine what the user would like to do with it.
  """
  if line.startswith('#'):
    return {"type": "comment", "contents": line}
  else:
    tokens = line.split()
    if len(tokens) < 2:
      raise ValueError("The line must be the name of the branch and have a "
                       "least one commit")

    branch, _, sourceBranch = tokens[0].partition(':')

    # If the user hasn't provided the name of the source branch assume it is
    # origin/master.
    if not sourceBranch:
      sourceBranch = 'origin/master'

    return {
      'type': 'newBranch',
      'newBranch': branch, 'sourceBranch': sourceBranch, 'commits': tokens[1:],
      }


def main():
  import fileinput

  for line in fileinput.input():
    data = input(line)
    if data['type'] == 'newBranch':
      del data['type']
      handle(**data)


if __name__ == '__main__':
  main()