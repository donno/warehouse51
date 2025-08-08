git-remote-base-rs
==================

An example project of a git remote written in Rust.

This one calls onto a git executable to read the example blobs.

See https://git-scm.com/docs/gitremote-helpers for details.

Notes
-----
`git clone base://foo/bar`

Results:
- Remote name: origin
- Remote URL: base://foo/bar
- Git directory set to the <cwd>/.git
    * This directory does not exist.
    * It would seem the remote helper is expected to create the directory.
      I expected the "clone" would handle that as it would be the same
      basic set-up for any remote.

Messages are then as follows:
1. capabilities
2. option progress true
3. option verbosity 1
4. object-format true
5. list
6. option check-connectivity true
7. option cloning true
8. fetch <commit> <ref>

### Ideas

- Provide trait / implementation of the [dumb protocol][1]. 

Key aspects are
- Way to list the references
- Way to list the packs
- Way to fetch/check if an object is loose

### Experiment
```
$ git remote-https origin https://github.com/git/git.git
capabilities
stateless-connect
fetch
get
option
push
check-connectivity
object-format
```

The `list` command doesn't seem to work instead this does:
`/usr/lib/git-core/git-ls-remote https://github.com/git/git.git`

Example:
```
f883596e997fe5bcbc5e89bee01b869721326109        refs/tags/v2.9.3
```

Testing pushing.
```
$ git remote add base-test base://git/
$ git push base-test main
capabilities
stateless-connect
fetch
get
option
push
check-connectivity
object-format
>>>>
option progress true
option verbosity 1
option object-format true
<<<<
push refs/heads/main:refs/heads/main
```

## References

* https://git-scm.com/docs/gitremote-helpers
* https://github.com/git/git/blob/v2.50.1/Documentation/gitprotocol-pack.adoc
* https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols

[1]: https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
