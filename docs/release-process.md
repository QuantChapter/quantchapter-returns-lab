# Release process

This is a maintainer procedure, not evidence that a particular release passed.
The linked GitHub Actions runs and release artifacts record actual outcomes.
No package is uploaded to PyPI by this repository's workflows.

## Scope and compatibility

Returns Lab is a pre-1.0 educational package. A release must keep its documented
input domain, units, conventions, failure behavior, and worked examples coherent.
Use a patch for a compatible correction and a minor version for an intentional
public behavior change. Explain any changed interpretation explicitly.

The runtime core has no third-party dependencies. The tracked `uv.lock` records
the development dependency resolution, including the build backend. Optional
plotting and notebook dependencies remain separate from the base installation.

## Before publication

1. Inspect the Git tree, branch, HEAD, and complete intended diff. Keep secrets,
   local paths, private platform code, and personal data out of the tree and history.
2. Review a numerical change against independently derived values and properties.
   Review teaching as a prepared first-time learner; retain complete comparisons
   for requested learner work. Agent review does not establish learner observation.
3. Set the version in `pyproject.toml` and the package's version declaration,
   update `CHANGELOG.md` and `.github/RELEASE_NOTES.md`, and intentionally refresh
   `uv.lock` when metadata or dependencies change.
4. Run the checks in [CONTRIBUTING.md](../CONTRIBUTING.md) from a clean environment.
   Resolve confirmed defects; do not lower the branch-coverage gate to hide a gap.
5. Inspect executed notebook outputs and figures. Check that saved results agree
   with the current code, input data, labels, and stated limitations.
6. Ensure the source archive and wheel build and their metadata pass Twine's
   strict checks. Install the wheel without dependencies in a fresh environment
   and execute the public API and CLI from outside the source checkout.
7. Merge the reviewed source into `main` and confirm the remote CI and CodeQL
   outcomes. A local pass does not stand in for a remote operating-system matrix.

The CI workflow tests Python 3.11 and 3.14 on Linux, Windows, and macOS, plus
Python 3.12 and 3.13 on Linux. Quality, notebook execution, packaging, and
dependency-audit jobs run separately. Dependencies are installed from the lockfile;
CI fails if the manifest and lock disagree. Build jobs use the locked Hatchling
backend without an independent build-time dependency resolution.

## Publish a version

Create a version tag only after the preceding gate is satisfied:

```bash
git tag -a v0.1.0 -m "QuantChapter Returns Lab 0.1.0"
git push origin v0.1.0
```

Use the actual next version in both commands for later releases. Do not move a
published tag. A correction requires a new version and an explanatory changelog
entry.

The release workflow calls the same CI workflow before its publication job.
It checks that the tagged commit belongs to `main` and the tag matches the
installed package version. It then builds the wheel and source archive, sets
`SOURCE_DATE_EPOCH` from the commit timestamp, checks the metadata, writes
`SHA256SUMS`, and creates GitHub build-provenance attestations before attaching
the artifacts to the release. Only this publication job requests write access
to releases, attestations, and its short-lived identity token.

After completion, inspect the public release, artifact names, checksums, tag,
and linked Actions runs without relying on the triggering push alone. Record
and fix any incomplete publication before claiming that the release is available.
If the workflow fails after creating an attestation but before publishing assets,
inspect the state and rerun the failed job only after resolving the cause; do not
overwrite an existing release or move its tag.

## Verify downloaded artifacts

Compare each downloaded file's SHA-256 digest with the matching entry in
`SHA256SUMS`. With an authenticated GitHub CLI, verify its build provenance:

```bash
gh attestation verify PATH_TO_DOWNLOADED_WHEEL --repo QuantChapter/quantchapter-returns-lab
```

Substitute the actual local wheel filename. Attestations identify the source and
workflow associated with a build; they do not prove mathematical correctness,
freedom from vulnerabilities, or suitability for a particular application.

## Repository settings

Settings require remote verification; workflow files cannot enable them alone.
Before reporting a protection as active, inspect its actual GitHub setting.

- Keep the repository public and the default branch `main`.
- Enable dependency alerts, secret scanning, push protection, and private
  vulnerability reporting where GitHub makes them available.
- Restrict ordinary workflow tokens to read access. Keep all action references
  pinned to verified full commit SHAs; review Dependabot updates before merging.
- Protect `main` with the CI checks that have actually reported. Keep force pushes
  and branch deletion disabled. Once another human maintainer is available,
  require an independent pull-request approval and code-owner review. A sole
  maintainer cannot provide an independent approval of their own pull request.
- Enable immutable releases if available before publishing a release that is
  intended to use that protection. Do not describe a release as immutable until
  the remote setting and release status are verified.
- Give collaborators only the access they need. Do not weaken controls to allow
  contributor code to access release credentials or security-sensitive workflows.

## Dependency and security updates

Dependabot checks the Actions references and uv dependencies weekly. Review the
upstream changes and lockfile, run the relevant gates, and assess the effect of
any advisory rather than suppressing the audit by default. See
[SECURITY.md](../SECURITY.md) for reporting and maintenance scope. An unavailable
advisory service is an incomplete audit, not a clean audit result.

## References

- [uv: GitHub Actions integration](https://docs.astral.sh/uv/guides/integration/github/)
- [uv: locking and syncing](https://docs.astral.sh/uv/concepts/projects/sync/)
- [GitHub: repository best practices](https://docs.github.com/en/repositories/creating-and-managing-repositories/best-practices-for-repositories)
- [GitHub: build-provenance attestations](https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations)
- [GitHub: supply-chain security and immutable releases](https://docs.github.com/en/code-security/concepts/supply-chain-security/supply-chain-security)

Initial action pins were resolved against the official upstream Git references
on 2 November 2026. Tags are explanatory comments; the full SHA is the executed
reference. Later updates require fresh upstream verification and CI evidence.
