torrent-docker
==============

This is about setting-up several containers with torrent program and one
container as a tracker. The intent is to setup an environment for demonstrating
how torrents work. The secondary goal is to see how you would build such a
thing with containers.

This is not a project for creating a container for downloading torrents or
seeding torrents.

Usage
-----

1. Create directory called "sources"
2. Copy files into that directory to create torrents from.
    * A torrent file will be created for each file in the directory.
    * A torrent file will be created for each directory in the directory.
      This enable a torrent to be created with multiple files in it.

Example
-------

* Set-up some files to share
    ```
    mkdir sources
    curl --location --output sources/alpine-standard-3.19.1-x86_64.iso https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/x86_64/alpine-standard-3.19.1-x86_64.iso
    ```
* Start the system:
    `podman compose up`
  Or
    `docker compose up`

How it works
------------

The compose file has three main services
- A BitTorrent tracker - A tracker is a server that keeps track of which seeds
  and peers are in the swarm. This uses [opentracker][0].
- Torrent creator - This takes a folder with files and directories and creates
  files from them. The resulting torrents are stored in a volume. Once all the
  torrents are created this service ends. This uses [mktorrent][1]
- Client - This is running [rtorrent][2]

DONE
----
- Created a container and service that seeds the file or at least it almost
  does. I sure it won't quite work due to the ports not being open to allow the
  leaches to connect.

TODO
----
- Sort out the ports for the seeder.
- Figure out how to actually control the seeding/sharing
    - The easily idea is to have one service "seeder" and the reset are
      "leachers".
    - The future way would be to have each client pick a file to seed.
- Figure out a way to monitor it. Currently using Flood is a nice way to see
  the torrent statue themselves.
- Set-up the system to run on its own network.

Other things
------------

- Initial mistake - missed the /announce on the tracker URL.
- The issue with the container saying "error opening terminal" was because it
  needs to be run in daemon mode rather than use the ncurse UI as that doesn't
  work when there is not an interactive session. The alternative would have
  been to run it in tmux.
- The challenge was getting rtorrent to load the torrents for the seeder. In
  the end the best thing was to to create the .rtorrent.rc to give full control
  over the settings.
- Current state is for the seeder instance, its able to load the torrent file
  automatically.
- Tried out Flood as a web UI. Worked well but for now running it in same
  container as rtorrent.
  - This has some potential for being quite neat for monitoring the set-up.
  - The future idea would be create a "volume" which ahs all the rpc sockets
    that each rtorrent instance has its own file and then start one flood UI
    that can access them all.

[0]: https://erdgeist.org/arts/software/opentracker/
[1]: https://github.com/pobrn/mktorrent
[2]: https://github.com/rakshasa/rtorrent