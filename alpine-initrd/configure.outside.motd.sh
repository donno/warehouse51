#!/bin/sh
# This is an example of the configure.outside script for the "motd" flavour
# which simply overwrites the message of the day that is baked into the
# image.
ROOT="$1"

. "$ROOT/etc/os-release"

cat << EOF > "$ROOT/etc/motd"
Welcome to $PRETTY_NAME!

This is a simple demonstration to test the ability to configure the instance
with a script.
EOF

# If this wasn't all written as shell scripts, then the idea would be this
# action would be more declarative so you could define the "files" and
# content.
# This approach does have advantage that it can be dynamic, such as the
# above example using the pretty name with the name of the OS and version.
