# Sneaky parity

There's some great built-in tools for site admins on GitHub Enterprise Server that's not as easy to get ahold of for GitHub Enterprise Cloud.  This is my handy collection of scripts to build on the APIs available for equivalent functionality.

![cloud-admins](/images/cloud-admins.jpg)

## Scripts

- [`org-admin-promote.py`](/org-admin-promote.py) replaces some of the functionality of `ghe-org-admin-promote` ([link](https://docs.github.com/en/enterprise-server@latest/admin/configuration/configuring-your-enterprise/command-line-utilities#ghe-org-admin-promote)), a built-in shell command on GHES that promotes an enterprise admin to own all organizations in the enterprise.  It also outputs a CSV file similar to the `all_organizations.csv` [report](https://docs.github.com/en/enterprise-server@latest/admin/configuration/configuring-your-enterprise/site-admin-dashboard#reports), to better inventory organizations.
