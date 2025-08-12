git-remote-base-rs
==================

An example project of a git remote written in Rust.

This one calls onto a git executable to read the example blobs.

See https://git-scm.com/docs/gitremote-helpers for details.

Testing
-------

Set the environment variable `GIT_SOURCE_DIRECTORY` to a directory containing
the git repositories you want to use as the remotes.

These are expected to have a working tree rather than bare.

### Cloning

`git clone base://git/<name>`

Where `<name>` is the name of a directory in `$GIT_SOURCE_DIRECTORY`.

### Pushing

If you clone from above, then you can push back there with
`git push origin <branch>`

It is recommended that you do don't do this against a repository that is
critical, as this is alpha software.

The known limitation is if the objects are in a pack file that the remote
doesn't know about.

#### Complete push

Create an empty 'remote' repository to test it with.
```
cd "$GIT_SOURCE_DIRECTORY"
git init --bare base-push/.git
```

The reason it iss `base-push/.git` rather than `base-push.git` is simply because
the implementation is simply expecting `.git` to be a subdirectory.

```
git remote add fresh base://git/base-push
git push fresh main
```

Recently complete
-----------------

* Download every object loose object needed during a fetch.
  * Currently, all packs are downloaded.
* Cloning a repository work - where it is cloned from already checked out
  repository.
* Uploading every loose object needed during a push.
  * Currently, all packs are uploaded if the object needed is not loose.

TODOs
-----
There are lots of things to do/handle but this list aims to track
the known things that are missing and are likely on the implement
soon list.

* Handle batch fetch
* Handle reading the pack file to find what objects it contains.
  This is instead of copying every pack file. That said, it might still be good
  idea to copy the idx file for every pack that way its there and doesn't need
  to be fetched again when it is time to use the corresponding pack.
* Write handler for uses libgit2 to manage references in the local repository,
  including on clone.

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
* https://git-scm.com/docs/pack-format

[1]: https://git-scm.com/book/en/v2/Git-Internals-Transfer-Protocols
