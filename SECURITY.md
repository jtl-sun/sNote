# Security Policy

## Reporting a vulnerability

Please do not include passwords, private notes, local paths, or access tokens in a public issue.
Report the smallest reproducible example and the affected sNote version to the repository owner.

## Terminal warning

sNote's integrated terminal executes commands with the same permissions as the current user.
Review commands before running them. Recursive remove commands permanently delete their targets.

## Privacy

sNote works locally and does not upload note content. User settings, recent-file history, and link
lists are stored in the operating system's user configuration directory and are excluded from the
repository.
