#!/bin/sh
#
# This ended up resembling the following a lot:
# https://github.com/marcov/firecracker-initrd/blob/master/container/build-initrd-in-ctr.sh

ALPINE_VERSION=3.21
ARCH=x86_64
BASE_URI="https://dl-cdn.alpinelinux.org/alpine/v$ALPINE_VERSION"
ENABLE_NETWORKING=0
FLAVOUR="$1"
if [ "$FLAVOUR" = "--help" ]; then
  echo "$0 - Create initial RAM filesystem for Alpine."
  echo "usage: $0 [flavour]"
  echo
  echo "  flavour - minimal, plain, standard"
  echo "            minimal is alpine-base broken down"
  echo "            plain [default] is alpine-base"
  echo "            standard is plain with util-linux, grep, nano and tmux"
  echo
  exit 2
fi

MINIMAL_PACKAGES="alpine-baselayout alpine-conf alpine-release busybox busybox-mdev-openrc busybox-openrc busybox-suid musl-utils openrc"
STANDARD_PACKAGES="alpine-base openrc"
# The alpine-base package depends on openrc so that is potential redundant.

if [ -z "$FLAVOUR" ]; then
  echo "Defaulting to the 'standard' variant."
  FLAVOUR="standard"
fi

# Additional packages are needed for networking.
if [ "$ENABLE_NETWORKING" -gt 0 ]; then
  STANDARD_PACKAGES="$STANDARD_PACKAGES iptables iproute2 openssh openssh-server-pam"
fi

[ "$FLAVOUR" = "minimal" ] && PACKAGES="$MINIMAL_PACKAGES" || PACKAGES="$STANDARD_PACKAGES"

if [ ! -f vmlinuz-virt ]; then
  echo Fetching Kernel
  wget "$BASE_URI/releases/$ARCH/netboot/vmlinuz-virt"
fi

echo Downloading base system with apk.
[ -f "packages.$FLAVOUR" ] \
  && xargs -a "packages.$FLAVOUR" echo "Packages: $PACKAGES" \
  || echo "Packages: $PACKAGES"

if [ -f "packages.$FLAVOUR" ]
then
  xargs -a "packages.$FLAVOUR" apk --arch "$ARCH" -X "$BASE_URI/main/" --root /rootfs --initdb --no-cache --allow-untrusted add $PACKAGES
elif [ "$FLAVOUR" = "minimal" ] || [ "$FLAVOUR" = "plain" ]
then
  # This is done second to allow for packages.minimal and packages.plain to
  # install additional packages if needed.
  apk --arch "$ARCH" -X "$BASE_URI/main/" --root /rootfs --initdb --no-cache --allow-untrusted add $PACKAGES
else
 echo "No package file found (packages.$FLAVOUR)."
 exit 1
fi

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

if [ -f users ]; then
  if [ "$ENABLE_NETWORKING" -gt 0 ]; then
    echo "Adding users."
    awk -f process-users.awk users > /rootfs/new-users
    chroot /rootfs /bin/sh /new-users
    rm /rootfs/new-users
  else
    echo "Adding users relies on SSH keys, so doesn't allow interactive login."
  fi
fi

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

# Perform configuration, outside the rootfs.
# This means if it is setting-up any additional services it can't run
# "rc-update add" but instead must use "ln -sf"
if [ -f "configure.outside.$FLAVOUR.sh" ]
then
  sh "configure.outside.$FLAVOUR.sh" /rootfs
fi


# Perform configuration, within the rootfs.
# This means if it is setting-up any additional services it can't run
# "rc-update add" but instead must use "ln -sf"
# Create the initial file system image.
if [ -f "configure.inside.$FLAVOUR.sh" ]
then
  cp "configure.inside.$FLAVOUR.sh" /rootfs
  chroot /rootfs /bin/sh "/configure.inside.$FLAVOUR.sh"
  rm "/rootfs/configure.inside.$FLAVOUR.sh"
fi

(cd /rootfs && find . -print0 | cpio --null --create --verbose --format=newc > /work/initrdfs && cd - >/dev/null) || exit 1

echo Usage example
echo qemu-system-x86_64 -m 512 -kernel vmlinuz-virt -initrd initrdfs
