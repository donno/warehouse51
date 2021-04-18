= FastImport

Parses the output of git fast-export and other tools designed to be used wit
git fast-import.

The format is documented here:
    https://www.git-scm.com/docs/git-fast-import#_input_format

== Getting started

* Expects Visual Studio 2019 - The build script doesn't account for GCC or
  Clang at this time.
* Expects [Ninja](https://ninja-build.org/) which can be [downloaded][1] from
  GitHub.
* $ `ninja`
* $ `ninja runimport`

This will export out the current repository in the fast-import format,
build the tool and then run the tool with the previous export.

It simply prints out a summary of the commands received.

== Licensing
This is licensed under the terms of the MIT License.
See LICENSE.txt for details.

Realistically, there really is only so many ways you could write this in C++
without getting to esoteric or obstructed. As such, I really don't mind
others using this.

The code itself is copyrighted by myself, however some of the comments have
been copied verbatim from Git's Documentation to aid in readability and
because again are only so many ways the sentences can be said.

== Intention

The intention is to produce a library, rather executable that can be used for
writing a "fast-import" like tool.

Supporting untrusted input is a non-goal, so a maliciously crafted repository
could break what is importing it. It is therefore the responsibility of the
caller to make sure any paths given to it stay within the bounds of
the repository. For example, watch out for a commit that try to write to
the ".git" folder. See --allow-unsafe-features in Git's [fast-import help][2].

[1]: https://github.com/ninja-build/ninja/releases
[2]: https://www.git-scm.com/docs/git-fast-import