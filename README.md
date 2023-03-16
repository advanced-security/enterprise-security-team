# Enterprise security management teams

This set of scripts provides some basics of organization governance to GitHub Enterprise (cloud or server) administrators.  The scripts will give you a list of all organizations in the enterprise as a CSV to work with programmatically, add you to all organizations as an owner, and can create/manage a team with the security manager role to see all GitHub Advanced Security alerts throughout the entire enterprise _without_ having admin rights to that code.

:information_source:  This uses the [security manager role](https://docs.github.com/en/organizations/managing-peoples-access-to-your-organization-with-roles/managing-security-managers-in-your-organization) and parts of the GraphQL API that is available in GitHub.com (free/pro/teams and enterprise), as well as GitHub Enterprise Server versions 3.5 and higher.

## Scripts

1. [`org-admin-promote.py`](/org-admin-promote.py) replaces some of the functionality of `ghe-org-admin-promote` ([link](https://docs.github.com/en/enterprise-server@latest/admin/configuration/configuring-your-enterprise/command-line-utilities#ghe-org-admin-promote)), a built-in shell command on GHES that promotes an enterprise admin to own all organizations in the enterprise.  It also outputs a CSV file similar to the `all_organizations.csv` [report](https://docs.github.com/en/enterprise-server@latest/admin/configuration/configuring-your-enterprise/site-admin-dashboard#reports), to better inventory organizations.
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

1. Edit the inputs at the start of the script as follows:
    - (for GHES) the API endpoint
    - Create a file called `token.txt` and save your token there to read it.
    - Add the enterprise slug, a string URL version of the enterprise identity.  It's easily available in the enterprise admin url (for cloud and server), e.g. `https://github.com/enterprises/ENTERPRISE-SLUG-HERE`.
    - (for the security manager team), the list of orgs output by `org-admin-promote.py` and the name of the security manager team and the team members to add.

1. Run them in the following order, deciding where to stop.
    1. `org-admin-promote.py` to add the enterprise admin to all organizations as an owner, creating a CSV of organizations.
    1. `manage-sec-team.py` to create a security manager team on all organizations and manage the members.
    1. `org-admin-demote.py` will remove the enterprise admin from all the organizations the previous script added them to.

## Assumptions

- The security manager team isn't already an existing team that's using team sync [for enterprise](https://docs.github.com/en/enterprise-cloud@latest/admin/identity-and-access-management/using-saml-for-enterprise-iam/managing-team-synchronization-for-organizations-in-your-enterprise) or [for organizations](https://docs.github.com/en/enterprise-cloud@latest/organizations/organizing-members-into-teams/synchronizing-a-team-with-an-identity-provider-group).  You may be able to edit the script a bit to make this work by adding an existing team to all orgs, but I wasn't going to dive deep into the weeds of identity management.

## Any extra info?

This is what a successful run looks like.  Here's the inputs:

- The enterprise admin is named `ghe-admin`.
- The security team is named `spy-stuff` and has two members `luigi` and `hubot`.
- The organizations break down as such:
  - `acme` org was already configured correctly.
  - `testorg-00001` needed the team created, with `ghe-admin` removed and `luigi` and `hubot` added.
  - `testorg-00002` was already created

```console
$ ./manage-sec-team.py 
Team spy-stuff updated as a security manager for acme!
Creating team spy-stuff
Team spy-stuff updated as a security manager for testorg-00001!
Removing ghe-admin from spy-stuff
Adding luigi to spy-stuff
Adding hubot to spy-stuff
Creating team spy-stuff
Team spy-stuff updated as a security manager for testorg-00002!
Removing ghe-admin from spy-stuff
Team spy-stuff updated as a security manager for testorg-00003!
```

## Architecture Footnotes

- Scripts that do things are in the root directory.
- Functions that do small parts are in `/src`, grouped roughly by what part of GitHub they work on.
- All Python code is formatted with [black](https://black.readthedocs.io/en/stable/) because it's simple and beautiful and no one needs to think about style.
- Python dependencies are minimal by default.  There are two, both kept up-to-date with [Dependabot](https://docs.github.com/en/code-security/dependabot/dependabot-version-updates/about-dependabot-version-updates).  You can check out the config file [here](.github/dependabot.yml) if you'd like.
  - [requests](https://pypi.org/project/requests/) is a simple and extremely popular HTTP library.
  - [defusedcsv](https://github.com/raphaelm/defusedcsv) is used over CSV to mitigate potential spreadsheet application exploitations based on how it processes user-generated data.  OWASP has written much more about CSV injection attacks on their website [here](https://owasp.org/www-community/attacks/CSV_Injection).
- The CSV files and TXT files are in the `.gitignore` file to not be accidentally committed into the repo.
