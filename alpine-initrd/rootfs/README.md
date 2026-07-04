Root File System
----------------

Building a root file system for the Linux kernel using Alpine.

Background
==========
Previously, created a initrd image as it was difficult to produce a hard drive
image due to the required kernel modules being hard to use in containers
or WSL.

On future investigation it is possible to build a root file system image (ext4)
within a container.

Building a complete disk image with GPT and two partitions, EFI System
Partition and the Linux root partition is also possible without requiring
any mounting of images.

Current
=======

### Tools Used
- sgdisk - a command-line GUID partition table (GPT) manipulator.
           This set up the overall disk image.
- dd - Copying the image that makes up each partition into the image.
- mcopy (from mtools) - Copying files into the vfat formatted image.
- mkfs.vfat (from dosfstools) - Formatting image as vfat.
  The version from busybox can only work with block devices.
- limine (from limine-efi-x86_64) - The boot loader.
- apk - For installing Alpine packages to form the root file system.
- [genimage](https://github.com/pengutronix/genimage) - Combine the vfat and
  ext4 along with the GPT partition table into a single hard drive image.

The `genimage` tool was used as I was unable to build the image without it as
the EFI System Partition wasn't being copied correctly and was being corrupted.
Put simply `genimage` replaces the `sgdisk` + `dd` approach until I can figure
out what is going wrong and can fix it.


### Running
Using QEMU with OVMF as the UEFI firmware and networking.
```sh
qemu-system-x86_64 -m 512 \
  -drive if=virtio,format=raw,file=alpine.img \
  -drive file=OVMF.fd,format=raw,if=pflash,unit=0
  -device virtio-net-pci,netdev=ournet -netdev user,id=ournet,ipv6=off
```

Future
======

* Replace `genimage`
* Replace shell script implementation with building a root file system using
  a Containerfile and running the Alpine tools directly during build.

