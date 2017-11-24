#!/usr/bin/env python
"""
Downloads wordlist from Debian package mirror.

NAME         : getdata
SUMMARY      : Downloads a wordlist from Debian package mirror.
COPYRIGHT    : (c) 2014 Sean Donnellan. All Rights Reserved.
LICENSE      : The MIT License (see LICENSE.txt for details)
"""

import contextlib
import urllib2
import os
import shutil
import sys
import tarfile


def importDebian():
  egg = 'data/python-debian.egg'

  if not os.path.exists(egg):
    print "Downloading python-debian"
    response  = urllib2.urlopen(
      "https://pypi.python.org/packages/2.7/p/python-debian/"
      "python_debian-0.1.21_nmu2-py2.7.egg")
    with open(egg, 'wb') as fw:
      shutil.copyfileobj(response, fw)

  sys.path.insert(0, egg)
  import debian
  return debian


def main():
  if os.path.exists('data') and not os.path.isdir('data'):
    print "data is not a directory."
    return 1
  elif not os.path.exists('data'):
    # Create the directory if it doesn't already exist.
    os.mkdir('data')

  mirror = 'http://http.us.debian.org/debian'
  dictionaries = {
    'wbritish-small': {
      'download': '/pool/main/s/scowl/wbritish-small_7.1-1_all.deb',
      'filename': 'british-english-small',
    },
    'wbritish-large': {
      'download': '/pool/main/s/scowl/wbritish-large_7.1-1_all.deb',
      'filename': 'british-english-large',
    },
    'wbritish-huge': {
      'download': '/pool/main/s/scowl/wbritish-huge_7.1-1_all.deb',
      'filename': 'british-english-huge',
    },

    # This possibly contains invalid words (as well ones that are very uncommon)
    'wbritish-insane': {
      'download': '/pool/main/s/scowl/wbritish-insane_7.1-1_all.deb',
      'filename': 'british-english-insane',
    },
  }

  # Choose which dictionary to use
  dictionary = dictionaries['wbritish-insane']
  dictionaryUri = mirror + dictionary['download']

  try:
    import debian
  except ImportError:
    debian = importDebian()

  from debian.arfile import ArFile

  debFile = 'data/wordlist.deb'

  print "Downloading " + dictionaryUri
  response  = urllib2.urlopen(dictionaryUri)
  with open(debFile, 'wb') as fw:
    shutil.copyfileobj(response, fw)

  ar = ArFile(debFile)
  data = [m for m in ar.members if 'data.tar.gz' == m.name][0]

  with tarfile.open(fileobj=data, mode="r:gz") as tar:
    wordlist = tar.extractfile('./usr/share/dict/' + dictionary['filename'])
    with open('data/wordlist.txt', 'w') as fw:
      shutil.copyfileobj(wordlist, fw)

  return 0

if __name__ == '__main__':
  exit(main())
