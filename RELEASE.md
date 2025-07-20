# Release Procedure
The basic procedure for releasing a new version of **hearing_profiler** consists of:
- Create a tag and update the change log
- Build and Publish the project

## Create a Tag

**hearing_profiler** uses semantic versioning. Update the version number in [hearing_profiler.py](hearing_profiler.py) according to changes since the previous tag.

**NOTE:** Ensure that the updated [hearing_profiler.py](hearing_profiler.py) is committed before creating the tag!

Create a tag with the current version, e.g. `0.0.9`.
```bash
git tag 0.0.9
```

## Update the ChangeLog

**hearing_profiler** uses `auto-changelog` to parse git commit messages and generate the `CHANGELOG.md`.

```bash
auto-changelog
git add CHANGELOG.md
git commit -m "Updating CHANGELOG"
git push
git push --tags
```

## Make a GitHub Release

Go to the GitHub project administration page and [publish a release](https://github.com/kev-m/hearing_profiler/releases/new) using the tag created, above.

Update the `release` branch:
```bash
git checkout release
git rebase development
git push -f
git checkout development
```

## Publishing the Package (Manual)

**NOTE:** This project is set up on GitHub for automatic publishing during the GitHub release process (above).
These instructions are for legacy purposes or manual publishing.

The library can be published using `flit` to build and publish the artifact.

**NOTE:** Ensure that PyPI configuration is set up correctly, e.g. that servers and authentication are defined in the `~/.pypirc` file.

The project details are defined in the `pyproject.toml` files. The version and description are defined in the top-level `__init__.py` file.

This project uses [semantic versioning](https://semver.org/).

Build and publish the library:
```bash
$ flit build
$ flit publish
```