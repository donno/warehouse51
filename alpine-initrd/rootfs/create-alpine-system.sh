#!/bin/sh
#
# Create a hard drive image containing ALpine Linux.
#
# Goal is to avoid needing to loop or network block devices.
#
# Tools used:
# - sgdisk - a command-line GUID partition table (GPT) manipulator.
#            This set up the the overall disk image.
# - dd - Copying the image that makes up each parittion into the image.
# - mcopy (from mtools) - Copying files into the vfat formatted image.
# - mkfs.vfat (from dosfstools) - Formatting image as vfat.
#   The version from busybox can only do block devices.
# - limine (from limine-efi-x86_64) - The boot loader.
#
# Running image:
# - qemu-system-x86_64 -m 512 -drive if=virtio,format=raw,file=.\images\alpine.img -drive file=OVMF.fd,format=raw,if=pflash,unit=0
# For networking add: -device virtio-net-pci,netdev=net-uDC8gBXd0 -netdev user,id=net-uDC8gBXd0,ipv6=off
#
# Features:
# - Networking - Uses dhcp for configuration via /etc/network/interfaces
#   DNS is configured via DHCP as well.
# - Alpine Package Keeper confiugred - Able to install nethack.
#
# Known issues:
# - The non genimage builder has corrupt EFI System Parittion
# - Hostname isn't set most likely the initrc is incomplete..
#   - This started wokring after setting up the networking in rc.
# - Missing tmpfs at /tmp - Need to configure /etc/fstab
# Future
# - Setup sshd - in progress (daemon is installed and running).
# - Set-up timezone
#
# Reference:
# https://gitlab.alpinelinux.org/alpine/alpine-conf/-/blob/master/setup-sshd.in

echo "Requires: apk add --no-cache dosfstools limine-efi-x86_64 mtools sgdisk e2fsprogs"

# get_alpine_release() is licenced under MIT License
#
# Copyright (c) 2022 Natanael Copa <ncopa@alpinelinux.org>
# https://gitlab.alpinelinux.org/alpine/alpine-conf/-/blob/3.22.0/setup-apkrepos.in?ref_type=tags
get_alpine_release() {
	# use the main version already configured, or get the version from /etc/alpine-release
	local version="$(grep -Eom1 '[^/]+/main/?$' "${ROOT}"etc/apk/repositories 2>/dev/null | grep -Eo '^[^/]+' \
		|| cat "${ROOT}"etc/alpine-release 2>/dev/null)"
	case "$version" in
		*_git*|*_alpha*) release="edge";;
		[0-9]*.[0-9]*.[0-9]*)
			# release in x.y.z format, cut last digit
			release=v${version%.[0-9]*};;
		v[0-9]*.[0-9]*)
            # release in vx.y format, keep as is
			release="${version}";;
		*)	# fallback to edge
			release="edge";;
	esac
}

# Set-up the repositories to use for apk.
# Usage: <rootfs> <mirror>
setup_apkrepos() {
  ROOT="$1"
  get_alpine_release  # This sets the release variable.
  mkdir -p "$1/etc/apk/" &&
    echo "$2/$release/main" > "$1/etc/apk/repositories"
    echo "$2/$release/community" >> "$1/etc/apk/repositories"
}

setup_networking() {
  local root="$1"
  cat >> "$1/etc/network/interfaces" << EOF
auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp
EOF

  # Automatically bring up the network.
  ln -sf networking             "$root/etc/init.d/net.eth0"
  ln -sf /etc/init.d/networking "$root/etc/runlevels/default/networking"
  ln -sf /etc/init.d/net.eth0   "$root/etc/runlevels/default/net.eth0"
  ln -sf sshd                   "$root/etc/init.d/sshd.eth0"
  ln -sf /etc/init.d/sshd.eth0  "$root/etc/runlevels/default/sshd.eth0"
}

# Create a directory with the root FS for the EFI System Partition (ESP).
create_boot_rootfs() {
  mkdir -p "$1/limine" "$1/EFI/BOOT/" && \
  cp /usr/share/limine/BOOTX64.EFI "$1/EFI/BOOT/BOOTX64.EFI" && \
  cat > "$1/limine/limine.conf" <<'EOF'
timeout: 10

/Alpine Linux (virt)
    protocol: linux
    kernel_path: boot():/limine/vmlinuz-virt
    module_path: boot():/limine/initramfs-virt
    kernel_cmdline: root=LABEL=ROOTFS rw modules=sd-mod,usb-storage,ext4
EOF

  # Copy kernel and initramfs to boot folder.
  cp "$2/boot/vmlinuz-virt" "$1/limine/vmlinuz-virt" &&
    cp "$2/boot/initramfs-virt" "$1/limine/initramfs-virt"
}

# Create a FAT32 formatted image to serve as the EFI System Partition (ESP).
#
# Usage: <source-directory> <rootfs-source-directory> <destination-image>
create_boot_image() {
  create_boot_rootfs "$1" "$2"

  dd if=/dev/zero of="$3" bs=1M count=128 && \
    mkfs.vfat -F 32 -n EFI -s 2 -v "$3" &&
    mcopy -i /images/efiboot.vfat -s /target-boot/* ::/
}

# Create a directory with the root FS for Linux system.
create_rootfs() {
  apk --arch x86_64 \
    -Xhttps://dl-cdn.alpinelinux.org/alpine/latest-stable/main/ \
    --root "$1" --initdb --no-cache --allow-untrusted \
    add alpine-base linux-virt curl nano openssh dosfstools
  setup_apkrepos "$1/" https://mirror.aarnet.edu.au/pub/alpine
  setup_networking "$1"
}

# Create a EXT4 formatted image to serve as the Linux parittion and root.
create_rootfs_image() {
  mkfs.ext4 -d "$1" -L ROOTFS "$2" 768M
}

# Assemble image into the final disk image.
#
# Usage: assemble_image <boot-image> <root-image> <destination-path>
assemble_image_v1() {
  # Re-create the file if it already exists.
  [ -f "$3" ] && rm "$3"

  # The disk is 900M not 896M to allow for the extra 2048 sectors (about 1M)
  # at the start and give some room at the end too for the backup.
  fallocate -l 900M "$3" && \
    sgdisk --zap-all "$3" \
    --new=1:0:+128M --typecode=1:ef00 --change-name=1:"EFI System Partition" \
    --new=2:0:0 --typecode=2:8300 --change-name=2:"Linux Root"

  # TOOD: the file size of "$1" could be verified to be 128M.
  # Likewise the size of both should be less than 900M.
  dd if="$1" of="$3" bs=512 seek=2024 conv=notrunc
  dd if="$2" of="$3" bs=512 seek=264192 conv=notrunc
}

assemble_image_v2() {
  # Paths to the files are already party of the genimage.cfg.
  genimage --outputpath /images --config genimage.cfg
}

[ ! -d /images ] && mkdir /images

create_rootfs /target-rootfs
create_boot_image /target-boot /target-rootfs /images/efiboot.vfat
create_rootfs_image /target-rootfs /images/rootfs.ext4

# This version is broken
#assemble_image /images/efiboot.vfat /images/rootfs.ext4 /images/system.img

assemble_image_v2

