#!/bin/sh
# Set-up an Alpine instance for running rootless Podman containers.
#
# Special thanks to Will Richardson for the following instructions:
# https://willhbr.net/2025/01/18/configure-rootless-podman-remote-on-alpine-linux/
# And
# https://wiki.alpinelinux.org/wiki/Podman

ROOT="$1"
USER="podman"

. "$ROOT/etc/os-release"
cat << EOF > "$ROOT/etc/motd"
Welcome to $PRETTY_NAME!

This is for running rootless containers with Podman.
EOF

ln -sf /etc/init.d/cgroups /rootfs/etc/runlevels/default/cgroups
ln -sf /etc/init.d/podman /rootfs/etc/runlevels/default/podman

echo tun >> "$ROOT/etc/modules"
echo "$USER:100000:65536" > "$ROOT/etc/subuid"
echo "$USER:100000:65536" > "$ROOT/etc/subgid"

# Set-up rootless mode.
echo "podman_user=\"$USER\"" >> "$ROOT/etc/conf.d/podman"

# TODO: Configure podman to write container images to /media/containers/ and
# for testing with Qemu look at creating a qcow image to use has -hda that is
# mounted at that location.

# The following error occurs:
# Error 0)
#   modprobe: module tun not found in modules.dep
# Error 1)
#   running `/usr/bin/newuidmap 1278 0 1001 1 1 100000 65536`:
#    newuidmap: Could not set capsn.
