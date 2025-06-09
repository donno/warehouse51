
Why initrd?
-----------

Creating a hard drive image proved to be difficult due to requiring kernel
modules not easily available in containers and WSL2.

Prior Art
---------

* A very minimal example in a [Gist](1) by [gdamjan](0).
* [firecracker-initrd](2) by [marcov](3) - The bulk of the script is based on this.

Features
--------

* Set-up user accounts with their authorised key. \
  See the section below for how to set it up.
* Supports three flavours, specified via the command line argument to the script.
  * minimal - same as below without apk-tools
  * plain - alpine-base
  * standard - same as above plus util-linux, grep, nano and tmux
* Support creating custom flavours which install extra packages. \
  Create a package.<flavour-name> file with one package per line.

When networking is enabled then iptables, iproute2 and openssh are installed.

Missing features
----------------

* No package mirror set-up for installing packages - Easily worked around by
  running `setup-apkrepos` if needed.
* Configurable hostname.
* Reduce the packages installed.
* Customisable install script that is run within chroot for extra packages.
* If there is no `apk` for the runner of the script then download and run the
  static binary instead.
* Allow networking to be toggled off or on at runtime without editing the
  script.

Known Issues
------------

### Missing Packages

For setup-alpine
- It expects "chrony" to be available to use that as NTP client.
  The Workaround is to use busybox.
- Setting up openssh also fails while it is already installed in the networking
  image, it needs the package to install.


How it Works
------------

The script is intended to be run in a Alpine container image as it currently
uses `apk` from the system.

* `apk` (Alpine Package Keeper) is used to populate the new root file system.
* The initial RAM disk for the netboot version is used to harvest the
  kernel modules for the newly created RAM disk.
* On boot devfs, procfs and sysfs is configured to be setup.
  In marcov's version, they have the `init` file be a shell script which simply
  mounts `/dev`, `/proc` and `/sys`.
* The password for root is set.
* For networking
    * The interface `eth0` and `lo` are set-up with the former being set to use
      dhcp and the latter being loopback.
    * The services, `mdev` and `hwdrivers` are configured to run on start-up
      to load the networking drivers.
    * When `eth0` is up, `sshd` is started.
* `/init` is set-up to be OpenRC.
* The image is put together with `cpio`.

### Users

Create a text file called `users` in the same directory as the script.

Start each line with the name of the user and the remaining with their SSH key
This assumes that users will SSH into the machine rather than login
interactively.
```
donno ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHMN+cIUeZaUdmT+kmwrGix5k9wXEUpHE2jQIma5JheW
pooh ssh-ed25519 ....
micky ssh-ed25519 ....
tintin ssh-ed25519 ....
```

The script will parse the file and add users and set-up their keys.

The plan was to have these accounts without passwords but sshd had other ideas,
as the accounts are locked if you don't set a password including when SSHing
so for now they have made-up passwords.

Also see https://arlimus.github.io/articles/usepam/

### Flavours

A new flavour is represented by up to three files:
* Package file - lists each package to install, one per line
* Configure script that runs outside the chroot [optional]
* Configure script that runs inside the chroot [optional]

To create a flavour, at a minimum create a package file.
* `package.<flavour>`
* `configure.outside.<flavour>.sh`
* `configure.inside.<flavour>.sh`

The configure script run outside will be passed the path to the root file
system that is being built.

Components
----------

- `/sbin/init` comes from `openrc`
- `/etc/init.d/mdev` comes from `busybox-mdev-openrc`

- If there is no internet then `apk-tools` is less useful unless you plan on
  sourcing it from another storage device. If you do have internet then you
  could fetch the static version to bootstrap installing apk-tools.

QEMU
----
* To enable networking `-net nic -net user`
* Forward port 22 (SSH) to 2222 on the host: `-net user,hostfwd=tcp::2222-:22`

Additional Notes
----------------

### Logging
Start the syslog service:
```sh
rc-service syslog start
```

Next tail the log:
```sh
tail -f /var/log/messages
```

The above was used to try to diagnose why I was unable to ssh in to a new
user account using a SSH key already set-up.

### Setting-up OpenRC
The script uses this approach:
```sh
ln -sf /etc/init.d/hwdrivers /rootfs/etc/runlevels/sysinit/
ln -sf /etc/init.d/mdev /rootfs/etc/runlevels/sysinit/
```
The alternative (and possibly more reliable) way to achive it would be to:
```sh
  chroot /rootfs /bin/sh -c 'rc-update add mdev sysinit'
  chroot /rootfs /bin/sh -c 'rc-update add hwdrivers sysinit'
```

The benefit of the first former example is it doesn't need to execute the
binaries within the root so it works when the host architecture is different
from the one for `/rootfs`.

### Next Stage

If you need to boot it from a virtual machine that requires an ISO or HDD
image then checkout [this superuser post](6),
"How to make an ISO file from bzImage and initramfs".

If I find myself needing this, I wll add a `mkiso.sh` here.

[0]: https://gist.github.com/gdamjan/1f260b58eb9fb1ba62d2234958582405
[1]: https://gist.github.com/gdamjan
[3]: https://github.com/marcov/
[4]: https://github.com/marcov/firecracker-initrd/
[5]: https://github.com/OpenRC/openrc
[6]: https://superuser.com/questions/1613122/how-to-make-an-iso-file-from-bzimage-and-initramfs
