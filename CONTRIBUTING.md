# Contributing

This document outlines the ways to contribute to `python-dateutil`. This is a fairly small, low-traffic project, so most of the contribution norms (coding style, acceptance criteria) have been developed ad hoc and this document will not be exhaustive. If you are interested in contributing code or documentation, please take a moment to at least review the license section to understand how your code will be licensed.

## Types of contribution
### Bug reports
Bug reports are an important type of contribution - it's important to get feedback about how the library is failing, and there's no better way to do that than to hear about real-life failure cases. A good bug report will include:

1. A minimal, reproducible example - a small, self-contained script that can reproduce the behavior is the best way to get your bug fixed. For more information and tips on how to structure these, read [StackOverflow's guide to creating a minimal, complete, verified example](https://stackoverflow.com/help/mcve).

2. The platform and versions of everything involved, at a minimum please include operating system, `python` version and `dateutil` version. Instructions on getting your versions:
    - `dateutil`: `python -c 'import dateutil; print(dateutil.__version__)'`
    - `Python`: `python --version`

3. A description of the problem - what *is* happening and what *should* happen.

While pull requests fixing bugs are accepted, they are *not* required - the bug report in itself is a great contribution.

### Feature requests

If you would like to see a new feature in `dateutil`, it is probably best to start an issue for discussion. You are welcome to prepare a pull request to start, but if it's going to be a lot of work, it's probably best to start by opening an issue so that you can know.

### Pull requests

If you would like to fix something in `dateutil` -  improvements to documentation, bug fixes, feature implementations, fixes to the build system, etc - pull requests are welcome! Try to keep your coding to [PEP 8 style](https://www.python.org/dev/peps/pep-0008/), with the minor modification that the existing `dateutil` class naming style does not use the CapWords convention.

The most important thing to include in your pull request are *tests* - please write one or more tests to cover the behavior you intend your patch to improve. Ideally, tests would use only the public interface - try to get 100% difference coverage using only supported behavior of the API.

## License

Starting December 1, 2017, all contributions will be assumed to be released under a dual license - the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0) and the [3-Clause BSD License](https://opensource.org/licenses/BSD-3-Clause) unless otherwise specified in the pull request.

All contributions before December 1, 2017 except those explicitly relicensed, are only under the 3-clause BSD license.
