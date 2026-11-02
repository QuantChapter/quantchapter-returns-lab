# Security policy

Returns Lab is a small, local educational package. Its runtime core does not
download market data, transmit inputs, execute supplied code, or need credentials.
Treat CSV files and any optional dependencies as untrusted input nonetheless.

## Reporting a concern

Use [GitHub's private vulnerability reporting](https://github.com/QuantChapter/quantchapter-returns-lab/security/advisories/new)
when it is available. Otherwise email **support@quantchapter.com** with the subject
`Returns Lab security report`. Include the affected version, reproduction steps,
impact, and a minimal synthetic example. Do not send credentials, private customer
data, or executable attachments. Do not file an exploitable vulnerability as a
public issue before discussing disclosure.

Reports are reviewed on a best-effort basis. There is no promised response time,
paid support agreement, bounty, certification, or guarantee of fitness for a
particular deployment. Coordinated disclosure and a minimal corrective release
are preferred when a report is confirmed.

## Supported versions and scope

Only the latest published `0.1.x` release is maintained. Upgrade to the latest patch
before reporting a problem. Earlier revisions remain available for reproducibility
but do not receive separate fixes. The project is pre-1.0 and has no long-term
support commitment.

Report incorrect calculations through the issue tracker unless the issue also
creates a security risk. Documented floating-point limits and deliberate validation
errors are part of the numerical contract, not promises to process arbitrary data.

## Maintainer practice

- Keep the runtime dependency-free and optional dependencies bounded and locked
  for development and continuous integration.
- Review dependency updates, security alerts, and changes to workflow permissions.
- Keep Actions dependencies pinned to full commit SHAs and credentials out of
  code, reports, notebooks, fixtures, and commit history.
- Use secret scanning, push protection, dependency alerts, and private reporting
  where available; a configuration file alone does not prove these are enabled.
- Never execute contributor code through `pull_request_target` or give ordinary
  pull-request CI write access.
- Publish a security advisory and release note when a fix warrants one.
