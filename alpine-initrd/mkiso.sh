#!/bin/sh
# Create a bootable ISO from Kernel image and initial RAM disk.
# Reference: https://superuser.com/a/1613141

if [ -z "$1" ]
then
  MODE="bios"
elif [ "$1" = "bios" ] || [ "$1" = "efi" ]
then
  MODE="$1"
else
  echo "Only supports bios or efi"
  exit 1
fi

if ! command -v genisoimage > /dev/null
then
  echo "missing: genisoimage program"
  echo "Install with: apk add cdrkit"
  exit 1
fi

if [ ! -f initrdfs ]
then
  echo "Missing inital RAM disk (initrdfs)."
  echo "Did you run mkramfs.sh first?"
  exit 2
fi

if [ ! -f vmlinuz-virt ]
then
  echo "Missing kernel image (vmlinuz-virt)."
  echo "Did you run mkramfs.sh first?"
  exit 2
fi

mkdir -p iso/boot/grub

if [ ! "$MODE" = "bios" ]
then
  echo "Only bios supported to date. efi coming soon."
  exit 4
fi
echo "Copying Kernel and initial RAM filesystem."
cp vmlinuz-virt iso/boot/
cp initrdfs iso/boot/

# If mkramfs.sh produced initrdfs-<flavour> this could
# produce a menu file which each one.

#echo "Creating grub image."
#grub-mkstandalone --format=i386-pc-eltorito --output=iso/boot/grub/core.img \
#  --core-compress=auto --locales=en --themes="" \
#  --install-modules="linux normal iso9660 biosdisk memdisk search tar ls" \
#  --modules="linux normal iso9660 biosdisk search" --fonts="" || echo "ailed to build grub image."
#cat /usr/lib/grub/i386-pc/cdboot.img iso/boot/grub/core.img > iso/boot/grub/grub.img

# The following works for BIOS
#
# This is likely from Grub Legacy rather than Grub 2 which the above would use.
wget -O iso/boot/grub/stage2_eltorito http://littleosbook.github.io/files/stage2_eltorito

echo "Copying Kernel and inital RAM filesystem."
cp vmlinuz-virt iso/boot/
cp initrdfs iso/boot/

# If mkramfs.sh produced initrdfs-<flavour> this could
# produce a menu file which each one.

echo "Creating grub menu"
# NOTE: This can be baked into the image above when Grub2 is used.
cat > iso/boot/grub/menu.lst << EOF
default 0
timeout 1
title Alpine Linux
kernel /boot/vmlinuz-virt
initrd /boot/initrdfs
EOF

genisoimage -R                        \
            -b boot/grub/stage2_eltorito \
            -no-emul-boot             \
            -boot-load-size 4         \
            -A os                     \
            -input-charset utf8       \
            -quiet                    \
            -boot-info-table          \
            -o myalpine.iso           \
            iso || exit 1

echo "Created myalpine.iso"

# TODO: Consider an option to add additional packages to
# the iso so they can be optional installed at runtime.
