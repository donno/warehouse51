#!/usr/bin/env python

__author__ = "Donno"
__copyright__ = "Copyright 2012, Donno (darkdonno@gmail.com)"
__credits__ = ["Donno"]
__license__ = "MIT"
__version__ = "0.1.0"
__maintainer__ = "Donno"
__email__ = "darkdonno@gmail.com"
__status__ = "Development"

# ^ http://epydoc.sourceforge.net/manual-fields.html#module-metadata-variables


import os
import itertools
import re

def collect_files(folder):
  def _include_file(filename):
    """A helper function to determine if a file should be included"""

    # If the caller was given the full path to the file perform this.
    #filename = os.path.basename(filepath)

    # Ignore any files that are are not the following types.
    accepted_file_types = ['.avi', '.mp4', '.sub', '.idx']
    correct_file_type = len(filter(filename.endswith, accepted_file_types)) == 1
    if not correct_file_type: return False

    # Ignore samples.

    is_sample = filename.startswith('sample-') or '.sample' in filename
    if is_sample or '-sample' in filename: return False

    return True

  firstChar = len(folder) + 1
  for dirPath, dirNames, fileNames in os.walk(folder):
    dirPath = dirPath[firstChar:] # Make dirPath relative to path

    newDirNames = []
    for name in dirNames:
      newDirNames.append(name)
    dirNames[:] = newDirNames # Modify dirNames so we don't recurse into excluded directories.

    for name in fileNames:
      path = os.path.join(dirPath, name)
      if _include_file(name):
        yield path


def tokenise_name(file_path):
  """Tokenises up the file_path to determine what it is"""
  show, season, episode = file_path.split('\\')

  return (show, season, episode)

def show_exists(folder, show):
  return os.path.isdir(os.path.join(folder, show))

def season_exists(folder, show, season):
  return os.path.isdir(os.path.join(folder, show, season))

def has_seasons(folder, show):
  """Returns True if the show has any season folders"""
  contents = os.listdir(os.path.join(folder, show))
  for name in contents:
    if not name.startswith('Season '): continue
    return os.path.isdir(os.path.join(folder, show, name))
  return False

def main():
  """The folder where the TV shows are downloaded into"""
  source_folder = "L:\\Downloads\\complete\\tv"

  """The folder where the TV shows are viewed from"""
  destination_folder = "L:\\Videos\\TV"


  interactive = True

  print 'Running with:'
  print '  Source: ' + source_folder
  print '  Destination: ' + destination_folder
  print '=' * 79

  missing_shows = set()
  missing_seasons = []

  for file_path in collect_files(source_folder):
    # Extract out the name of the show, season and episode.
    try:
      show, season, episode = tokenise_name(file_path)
    except ValueError:
      continue

    # Determine if the show exists
    if not show_exists(destination_folder, show):
      if show not in missing_shows:
        print "W: '" + show + "' doesn't exist in the destination"
        missing_shows.add(show)
      continue

    # Determine if the show has any season folders or if its all in the root
    # of the show.
    any_seasons = has_seasons(destination_folder, show)

    # Determine if the season for the show exists if the destination uses
    # seasons and doesn't just stock pile in the root.
    if any_seasons and not season_exists(destination_folder, show, season):
      if os.path.join(show, season) not in missing_seasons:
        print "W: " + season + " is missing for '" + show + "'"
        missing_seasons.append(os.path.join(show, season))
      continue

    if any_seasons:
      destination_file_path = os.path.join(destination_folder, show, season, episode)
    else:
      # The show doesn't use seasons at the moment.
      destination_file_path = os.path.join(destination_folder, show, episode)

    if os.path.exists(destination_file_path):
      print "W: '%s' already exists not moving" % destination_file_path
      continue

    print 'Moving ' + os.path.basename(file_path)

    # :WARNING: The following requires the two folders are on the same harddrive
    #os.rename(os.path.join(source_folder, file_path), destination_file_path)

  
  if interactive:
    print '=' * 79
    print 'Interactive mode'
    
    print 'Create show folders'
    for show in missing_shows:
      
      while True:
        input = raw_input("Create '%s' [Y/N]> " % show).lower()
        if input == 'y':
          print "Creating folder for '%s'" % show
          os.mkdir(os.path.join(destination_folder, show))
          break
        elif input == 'n':
          break
        else:
          print "Sorry, you must enter either 'Y' or 'N'"
    
    print 'Create seasons for show'

    for season_path in missing_seasons:
      show, season = season_path.split('\\')

      while True:
        input = raw_input("Create %s for '%s' [Y/N]> " % (season, show)).lower()
        if input == 'y':
          print "Creating folder for %s of '%s'" % (season, show)
          os.mkdir(os.path.join(destination_folder, season_path))
          break
        elif input == 'n':
          break
        else:
          print "Sorry, you must enter either 'Y' or 'N'"
    
if __name__ == '__main__':
  main()