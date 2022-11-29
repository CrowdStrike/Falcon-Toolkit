<!-- omit in toc -->
# Contributing to Falcon Toolkit

<!-- omit in toc -->
## Getting started

_Welcome!_ We're excited you want to take part in the Falcon Toolkit community!

Please review this document for details regarding getting started with your first contribution, packages you'll need to install as a developer, and our Pull Request process. If you have any questions, please let us know by
posting your question in the [discussion board](https://github.com/CrowdStrike/Falcon-Toolkit/discussions).

### Before you Begin

- Have you read the [Code of Conduct](CODE_OF_CONDUCT.md)? The Code of Conduct helps us establish community norms and how they'll be enforced.

### Table of Contents

- [How you can contribute](#how-you-can-contribute)
  - [Bug reporting](#bug-reporting-is-handled-using-githubs-issues)
- [Pull Requests](#pull-requests)
  - [Linting](#linting)
  - [Pull Request Contents](#pull-request-contents)
  - [Approving / Merging](#approval--merging)
- [Suggestions](#suggestions)

## How you can contribute

- See something? Say something! Submit a [bug report](https://github.com/CrowdStrike/Falcon-Toolkit/issues) to let the community know what you've experienced or found. Bonus points if you suggest possible fixes or what you feel may resolve the issue. For example: "_Attempted to use the XYZ command but it errored out._" Could a more descriptive error code be returned?
- Join the [discussion board](https://github.com/CrowdStrike/Falcon-Toolkit/discussions) where you can:
  - [Interact](https://github.com/CrowdStrike/Falcon-Toolkit/discussions/categories/general) with other members of the community
  - Suggest [new functionality](https://github.com/CrowdStrike/Falcon-Toolkit/discussions/categories/ideas)
  - Provide [feedback](https://github.com/CrowdStrike/Falcon-Toolkit/discussions/categories/q-a)
  - [Show others](https://github.com/CrowdStrike/Falcon-Toolkit/discussions/categories/show-and-tell) how you are using Falcon Toolkit today
- Submit a [Pull Request](#pull-requests)

### Bug reporting is handled using GitHub's issues

We use GitHub issues to track bugs. Report a bug by opening a [new issue](https://github.com/CrowdStrike/Falcon-Toolkit/issues).

## Pull Requests

### All contributions will be submitted under the MIT licence

When you submit code changes, your submissions are understood to be under the same [MIT licence](LICENSE) that covers the project.
If this is a concern, contact the maintainers before contributing.

### Linting

All submitted code must meet minimum linting requirements.

- We use [`flake8`](https://flake8.pycqa.org) and [`pylint`](https://www.pylint.org) for linting, and [`pydocstyle`](https://pydocstyle.org) to ensure that docstrings comply with best practices.
- All code that is included within the installation package must pass linting workflows when the Pull Request checks have completed.
  - You will be asked to correct linting errors before your Pull Request will be approved.
- Samples are checked for linting, but failures will not stop builds at this time.

### Pull Request Contents

When opening a pull request, please ensure the following details are included:

- Is this a breaking change?
- Are all new or changed code paths covered by unit testing, where appropriate?
- A complete listing of issues addressed or closed with this change.
- A complete listing of any enhancements provided by this change.
- Any usage details developers may need to make use of this new functionality.
  - Does additional documentation need to be developed beyond what is listed in your Pull Request?
- Any other salient points of interest.

### Approval / Merging

All Pull Requests must be approved by at least one maintainer. Once approved, a maintainer will perform the merge and execute any backend processes related to package deployment. At this time, contributors _do not_ have the ability to merge to the `main` branch.

## Suggestions

If you have suggestions on how this process could be improved, please let us know by [posting an issue](https://github.com/CrowdStrike/Falcon-Toolkit/issues).
