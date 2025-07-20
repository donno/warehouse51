Alpine WSL
==========

Examples which create your own Alpine distributions for Windows Subsystem for
Linux 2. The key aspect of this is to crete a rootfs tarball which can be
imported/installed via the `wsl` tool.

How
---

The tool behind this implementation is [`apko`][0] by [Chainguard][1].

There is [documentation][2] for the the file format.

### From Linux
```sh
wget https://github.com/chainguard-dev/apko/releases/download/v0.29.7/apko_0.29.7_linux_amd64.tar.gz
tar xf apko_0.29.7_linux_amd64.tar.gz
./apko_0.29.7_linux_amd64/apko build-minirootfs alpine-base.yaml alpine-base.tar.gz
```

### Via Container
Build within a container.
```
podman run -v .:/host cgr.dev/chainguard/apko:latest build-minirootfs /host/alpine-base.yaml /host/alpine-base.tar.gz
podman run -v .:/host cgr.dev/chainguard/apko:latest build-minirootfs /host/wolfi-base.yaml /host/wolfi-base.tar.gz
podman run -v .:/host cgr.dev/chainguard/apko:latest build-minirootfs /host/wolfi-podman.yaml /host/wolfi-podman.tar.gz
```

Warning: `ghcr.io/chainguard-dev/apko/apko:latest` is out-dated and no longer
seems to be maintained instead `cgr.dev/chainguard/apko` is the registry that
is updated.

Basic Alternative
-----------------
This is the original approach I used before coming across `apko`. The basic
idea is use `apk` to create a root file system from packages and then create a
tar from it.
```
podman run --rm -v .:/host --entrypoint /bin/sh public.ecr.aws/docker/library/alpine:3.22.0 -c "apk --arch x86_64 -X https://dl-cdn.alpinelinux.org/alpine/latest-stable/main -U --allow-untrusted --root /rootfs --initdb add alpine-base && touch /rootfs/etc/fstab && tar c -z -C /rootfs  --numeric-owner -f /host/alpine-base.tar.gz ."
wsl --install --name AlpineBase --from-file .\alpine-base.tar.gz
```

Why
---
Why use `apko` instead of the above approach?

The configuration file for `apko` takes care of defining how to configure the
set-up.

It supports providing the list of repositories and packages.

Questions
---------
Is it possible to have `/var/tmp` for the `wolfi-podman` distribution, use
`tmpfs` instead of being a plain-old directory. Based on the format of `paths`
it doesn't seem possible using that syntax directly and instead would require
the `fstab` to be created.

[0]: https://apko.dev/
[1]: https://www.chainguard.dev/
[2]: https://github.com/chainguard-dev/apko/blob/v0.29.7/docs/apko_file.md
