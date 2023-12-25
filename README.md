![image](https://github.com/Asugawara/pgcs/actions/workflows/run_test.yml/badge.svg)
![PyPI](https://img.shields.io/pypi/v/pgcs?color=green)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pgcs)
![GitHub](https://img.shields.io/github/license/Asugawara/pgcs)


# Pgcs

**Pgcs** is an intuitive TUI tool designed to simplify your interaction with Google Cloud Storage. Stay in your coding zone by navigating directories, searching files (with case-insensitive support), and previewing files all from your terminal. Easily save paths to clipboard or download files with straightforward keyboard shortcuts. Experience a seamless Cloud Storage interaction right from your terminal; no more swapping to a browser.

# Features
- Navigate through directories with left and right arrows
- Peco-like search UI
- Case-insensitive search
- Preview of the file is available
- Press 'ctrl-p' to save the path to clipboard
- Press 'ctrl-d' to download


# Installation

```bash
$ pip install pgcs
```

# Usage
> [!IMPORTANT]
> Both `gcloud auth login` and `gcloud auth application-default login` are required.

command | description
-- | --
`pg` or `pg traverse` | navigate through Google Cloud Storage directories
`pg pref --init` | initialize or reset preferences file
`pg pref <key> <value>` | set preference with key to value

> [!Note]
> If you want to use clipboard functionality on Linux without a GUI, you need to execute the following. Below is an example.
```bash
$ sudo apt-get install xvfb
$ sudo apt-get install xclip
$ Xvfb :99 -screen 0 1280x720x16 &
$ export DISPLAY=:99
```

# Versioning
This repo uses [Semantic Versioning](https://semver.org/).

# License
**pgcs** is released under the MIT License. See [LICENSE](/LICENSE) for additional details.
