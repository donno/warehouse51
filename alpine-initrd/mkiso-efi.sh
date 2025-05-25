#!/bin/sh
# Create a bootable ISO from Kernel image and initial RAM disk.
#
# This creates an ISO for EFI
#
# It would be nice to combine the BIOS + EFI into single ISO.
#
# Packages:
#   apk add grub grub-efi mtools
#
# =============================================
# DISCLAIMER:
#
# This doesn't boot correctly.
#
# =============================================

ARCH=x86_64

if ! command -v grub-mkimage > /dev/null
then
  echo "missing: grub-mkimage  program"
  echo "Install with: apk add grub"
  exit 1
fi

if ! command -v mcopy > /dev/null
then
  echo "missing: mcopy"
  echo "Install with: apk add mtools"
  exit 1
fi

if ! command -v xorrisofs > /dev/null
then
  echo "missing: xorrisofs"
  echo "Install with: apk add xorriso"
  exit 1
fi

if [ ! -f "/usr/lib/grub/$ARCH-efi/modinfo.sh" ]
then
  echo "missing: grub-efi package"
  echo "Install with: apk add grub-efi"
  echo ""
  echo "Alpine only has the parts for the same arch."
  # This could be extended to install/download the copy of grub-efi for
  # $ARCH.
  # See:
  # https://github.com/alpinelinux/aports/blob/5d60653f576843a1038495f93912c45fe4df2757/scripts/mkimg.base.sh#L200
  exit 1
fi

mkdir -p iso/efi/boot
mkdir -p iso/boot/grub

echo "Copying Kernel and initial RAM filesystem."
cp vmlinuz-virt iso/boot/
cp initrdfs iso/boot/

# This stub is baked into the image.
cat << EOF > /tmp/grub-stub.cfg
insmod linux

search --no-floppy --set root --label alpine-virt
set prefix=(\$root)/boot/grub

EOF

grub_mod="all_video disk part_gpt part_msdos linux normal configfile search search_label efi_gop fat iso9660 cat echo ls test true help gzio"
if [ "$ARCH" = "x86-64" ]
then
  grub_mod="$grub_mod multiboot2 efi_uga"
fi

# The filename of the efi file needs to match the specific arch.
# x86_64 -> x64, arm64 -> aa64.
grub-mkimage \
		--config="/tmp/grub-stub.cfg" \
		--prefix="/boot/grub" \
		--output="iso/efi/boot/bootx64.efi" \
		--format="$ARCH-efi" \
		--compression="xz" \
    $grub_mod || exit 1

cat > iso/boot/grub/grub.cfg << EOF
timeout=1
menuentry "Alpine Linux"
{
  linux /boot/vmlinuz-virt
  initrd /boot/initrdfs
}
EOF

# Create the EFI boot partition image
mformat -i iso/boot/grub/efi.img -C -f 1440 -N 0 ::
mcopy -i iso/boot/grub/efi.img -s iso/efi ::
#
# Alternative:
# echo "Create EFI System Partition (ESP) image"
# mformat -i iso/efi/boot/efiboot.img -C -f 1440 -N 0 ::
# mmd -i iso/efi/boot/efiboot.img ::EFI
# mmd -i iso/efi/boot/efiboot.img ::EFI/BOOT
# mcopy -i iso/efi/boot/efiboot.img iso/EFI/BOOT/bootx64.efi ::EFI/BOOT/bootx64.efi

efiboot="
    -efi-boot-part
    --efi-boot-image
    -e boot/grub/efi.img
    -no-emul-boot
    "

xorrisofs \
--output myalpine-efi.iso \
-full-iso9660-filenames \
-joliet \
-rational-rock \
-sysid LINUX \
-volid "alpine-virt" \
    -follow-links \
-hide-rr-moved \
-no-emul-boot \
$efiboot \
iso || exit 1

echo "Created myalpine-efi.iso"
