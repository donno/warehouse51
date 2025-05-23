
Why initrd?
-----------

Creating a hard drive image proved to be difficult due to requiring kernel
modules not easily available in containers and WSL2.

Prior Art
---------

* A very minimal example in a [Gist](1) by [gdamjan](0).
* [firecracker-initrd](2) by [marcov](3) - The bulk of the script is based on this.

Missing features
----------------

* No package mirror set-up for installing packages - Easily worked around by
  running `setup-apkrepos`if needed.
* Configurable hostname.
* Set-up user accounts, possibly with their authorised key.
* Reduce the packages installed.
* Customise to include extra packages.
* If there is no `apk`, download and run the static binary instead.

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

Components
----------

- `/sbin/init` comes from `openrc`
- `/etc/init.d/mdev` comes from `busybox-mdev-openrc`

Additional Notes
----------------

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
