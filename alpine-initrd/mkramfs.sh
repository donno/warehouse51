#!/bin/sh
#
# This ended up resembling the following a lot:
# https://github.com/marcov/firecracker-initrd/blob/master/container/build-initrd-in-ctr.sh

ALPINE_VERSION=3.21
ARCH=x86_64
BASE_URI=https://dl-cdn.alpinelinux.org/alpine/v$ALPINE_VERSION
EXTRA_PACKAGES="nano tmux"
ENABLE_NETWORKING=1

if [ ! -f vmlinuz-virt ]; then
  echo Fetching Kernel
  wget "$BASE_URI/releases/$ARCH/netboot/vmlinuz-virt"
fi

echo Downloading base system with apk.

apk --arch "$ARCH" -X "$BASE_URI/main/" --root /rootfs --initdb --no-cache --allow-untrusted add alpine-base openrc util-linux grep $EXTRA_PACKAGES


# Configure startup
cp /rootfs/sbin/init /rootfs/init
echo "ttyS0" >> /rootfs/etc/securetty
ln -sf /etc/init.d/devfs  /rootfs/etc/runlevels/boot/devfs
ln -sf /etc/init.d/procfs /rootfs/etc/runlevels/boot/procfs
ln -sf /etc/init.d/sysfs  /rootfs/etc/runlevels/boot/sysfs
ln -sf agetty             /rootfs/etc/init.d/agetty.ttyS0
ln -sf /etc/init.d/agetty.ttyS0 /rootfs/etc/runlevels/default/agetty.ttyS0

[ ! -d /rootfs/lib/modules ] && mkdir /rootfs/lib/modules
# The goal is the copy the modules the initial RAM disk from netboot version.

# This is required for networking but isn't required for for
.  copy-modules.sh

# Set root password.
chroot /rootfs /bin/sh -c 'adduser root; echo -e "root\nroot" | passwd root'
# Consider setting up additional users with the SSH keys.

# Configure the networking
if [ "$ENABLE_NETWORKING" -gt 0 ]; then
  ln -sf networking             /rootfs/etc/init.d/net.eth0
  ln -sf /etc/init.d/networking /rootfs/etc/runlevels/default/networking
  ln -sf /etc/init.d/net.eth0   /rootfs/etc/runlevels/default/net.eth0
  ln -sf sshd                   /rootfs/etc/init.d/sshd.eth0
  ln -sf /etc/init.d/sshd.eth0  /rootfs/etc/runlevels/default/sshd.eth0

  # Set-up mdev as the device manager. If a full blown desktop environment
  # then it is not recommended. See https://wiki.alpinelinux.org/wiki/Mdev
  ln -sf /etc/init.d/hwdrivers /rootfs/etc/runlevels/sysinit/

  # This needs: apk add busybox-mdev-openrc
  ln -sf /etc/init.d/mdev /rootfs/etc/runlevels/sysinit/
  # Alternate approach, but this requires that the host can run `rc-update`
  # which could be for a different architecture.
  #chroot /rootfs /bin/sh -c 'rc-update add mdev sysinit'

  # Configure networking
  # For details see: https://wiki.alpinelinux.org/wiki/Configure_Networking
  # Specially, if static IP appeals to you.
  cat >> /rootfs/etc/network/interfaces << EOF
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF

fi

# Create the initial file system image.
(cd /rootfs && find . -print0 | cpio --null --create --verbose --format=newc > /work/initrdfs && cd - >/dev/null;)

echo Usage example
echo qemu-system-x86_64 -m 512 -kernel vmlinuz-virt -initrd initrdfs
