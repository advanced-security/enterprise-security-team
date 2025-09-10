# Enterprise security management teams

These scripts provide an emulated Enterprise security manager team to GitHub Enterprise (cloud or server) administrators by using the existing organization security manager role.

The scripts will give you a list of all organizations in the enterprise as a CSV to work with programmatically, add you to all organizations as an owner, and can create/manage a team with the security manager role to see all GitHub Advanced Security alerts throughout the entire enterprise _without_ having admin rights to that code.

:information_source:  This uses the [security manager role](https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization) and parts of the GraphQL API that is available in GitHub.com (free/pro/teams and enterprise), as well as GitHub Enterprise Server versions 3.5 and higher.

## Scripts

1. [`org-admin-promote.py`](/org-admin-promote.py) replaces some of the functionality of [`ghe-org-admin-promote`](https://docs.github.com/en/enterprise-server@latest/admin/configuration/configuring-your-enterprise/command-line-utilities#ghe-org-admin-promote), a built-in shell command on GHES that promotes an enterprise admin to own all organizations in the enterprise.  It also outputs a CSV file similar to the `all_organizations.csv` [report](https://docs.github.com/en/enterprise-server@latest/admin/configuration/configuring-your-enterprise/site-admin-dashboard#reports), to better inventory organizations.
1. [`manage-sec-team.py`](/manage-sec-team.py) creates a team in each organization, assigns it the security manager role, and then adds the people you want to that team (and removes the rest).
1. [`org-admin-demote.py`](/org-admin-demote.py) takes the text file of orgs that the user wasn't already an owner of and "un-does" that promotion to org owner.  The goal is to keep the admin account's notifications uncluttered, but running this is totally optional.

## How to use it

You need to be an enterprise administrator to use these scripts!

1. Read :point_up: and decide what you want to do.
1. Create a personal access token ([directions](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)) with the `enterprise:admin` scope.
1. Clone this repository to a machine that has Python 3 installed.
1. Install the requirements.

    ```shell
    python3 -m pip install --upgrade pip
    pip install -r requirements.txt
    ```

1. Choose inputs as arguments to the script as follows:

    - the server URL (for GHES, EMU, or data residency) in `--github-url`
      - For GHEC this is not required.
    - call the script with the correct GitHub PAT
      - place it in `GITHUB_TOKEN` in your environment, or
      - create a file and save your token there to read it, and call the script with the `--token-file` argument
    - use the enterprise slug as the first argument in the promote/demote scripts
      - this is string URL version of the enterprise identity.  It's available in the enterprise admin url (for cloud and server), e.g. `https://github.com/enterprises/ENTERPRISE-SLUG-HERE`.
    - for the security manager team script:
      - use the list of orgs output by `org-admin-promote.py` in `--unmanaged-orgs`
      - put the name of the security manager team and the team members to add in `--team-name` and `--team-members`.
      - If you are using GHES 3.15 or below, please use the `--legacy` flag to use the legacy security managers API.

1. Run them in the following order:

    1. `org-admin-promote.py` to add the enterprise admin to all organizations as an owner, creating a CSV of organizations.
    1. `manage-sec-team.py` to create a security manager team on all organizations and manage the members.
    1. `org-admin-demote.py` will remove the enterprise admin from all the organizations the previous script added them to.

## Assumptions

- The security manager team isn't already an existing team that's using team sync [for enterprise](https://docs.github.com/en/enterprise-cloud@latest/admin/identity-and-access-management/using-saml-for-enterprise-iam/managing-team-synchronization-for-organizations-in-your-enterprise) or [for organizations](https://docs.github.com/en/enterprise-cloud@latest/organizations/organizing-members-into-teams/synchronizing-a-team-with-an-identity-provider-group).

## Any extra info?

This is what a successful run looks like.  Here's the inputs:

- The enterprise admin is named `ghe-admin`.
- The security team is named `security-managers` (the default) and has two members `luigi` and `hubot`.
- The organizations break down as such:
  - `acme` org was already configured correctly.
  - `testorg-00001` needed the team created, with `ghe-admin` removed and `luigi` and `hubot` added.
  - `testorg-00002` was already created

```console
$ ./manage-sec-team.py --sec-team-members luigi hubot
✓ Team security-managers updated as a security manager for acme
Creating team security-managers
✓ Team security-managers updated as a security manager for testorg-00001
Removing ghe-admin from security-managers
Adding luigi to security-managers
Adding hubot to security-managers
Creating team security-managers
✓ Team security-managers updated as a security manager for testorg-00002
Removing ghe-admin from security-managers
✓ Team security-managers updated as a security manager for testorg-00003
```

## Architecture Footnotes

- Scripts that do things are in the root directory.
- Functions that do small parts are in `/src`, grouped roughly by what part of GitHub they work on.
- All Python code is formatted with [black](https://black.readthedocs.io/en/stable/) because it's simple and beautiful and no one needs to think about style.
- Python dependencies are minimal by default.  There are two, both kept up-to-date with [Dependabot](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates).  You can [check out the config file](.github/dependabot.yml) if you'd like.
  - [requests](https://pypi.org/project/requests/) is a simple and extremely popular HTTP library.
  - [defusedcsv](https://github.com/raphaelm/defusedcsv) is used over CSV to mitigate potential spreadsheet application exploitations based on how it processes user-generated data.  OWASP has [written much more about CSV injection attacks on their website](https://owasp.org/www-community/attacks/CSV_Injection).
- The CSV files and TXT files are in the `.gitignore` file to not be accidentally committed into the repo.
