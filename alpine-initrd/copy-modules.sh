#!/bin/sh
if [ -z "$BASE_URI" ]; then
  echo "This is expected to be run from mkramfs.sh"
  exit 1
fi

echo Fetching initial disk image
wget $BASE_URI/releases/$ARCH/netboot/initramfs-virt || exit $?

echo Extract initial disk image for its kernel modules.
(mkdir /tmp/original && cd /tmp/original && zcat /work/initramfs-virt | cpio -i)

echo Copy the kernel modules to the new rootfs.
cp -r /tmp/original/lib/modules /rootfs/lib/

# Requires mkinitfs to be installed.
KERNEL_VERSION=$(find /rootfs/lib/modules/ -maxdepth 1 -mindepth 1 -exec basename {} \;)
echo "Kernel version: $KERNEL_VERSION"

