# THIS FILE IS DEPRECATED AND KEPT FOR REFERENCE

# TODO: branch will be switched from o8 to master like all other branches for master repo fundraising_studio

# FS-Online odoo code base
This repository is used as a codebase for FS-Online instances and the related setup tools. 
The *o[0-9]+* branches of this repo are always deploy-able production ready branches.

## CONVENTIONS

#### Branches:
**The default latest stable branch is called o[0-9]+ e.g.: o8 or o9.** where the number after o stands for the odoo version. 
The other branches in the github repository are development branches in the form of o8_[ISSUENUMBER]_[OPTIONALDESCRIPTION] e.g.: o8_123 or o8_123_shoptemplates or without an Github Issue o8_[DESCRIPTION]

Examples:
- o8 = Master Branch for FS-Online for odoo Version 8
- o9 = Master Branch for FS-Online for odoo Version 9
- o8_256 = Development or Bugfix Branch related to github issue 256 to be merged into o8 Master Branch
- o8_fixsendmail = Development or Bugfix Branch without an issue to be merged into o8 Master Branch
- o9_123_addfreetoshop = Development or Bugfix Branch related to github issue 123 to be merged into o9 Master Branch with optional description

#### Release Tags
Release tags must have the form [BRANCH]r[COUNTER] e.g.: **o8r1** or **o9r23**

## Odoo Tools
Simple setup and maintenance through odoo-tools.sh. **odoo-tools.sh** is a simple setup script that is able to:

- **prepare** (DEPRICATED by Saltstack) an ubuntu 14.04 LTS server to run odoo v8 (libs, tools, settings)
- **setup**/download (DEPRICATED by Saltstack) the odoo code base for odoo v8 from github
- **newdb** (DEPRICATED by Saltstack) create a new odoo instance:
    - linux user
    - database creation
    - postgres user
    - server.conf und server.init
    - etherpad
    - owncloud
    - nginx setup (match urls to instance via vhosts) and setup default URLs e.g.: ahch.datadialog.net, aswidget.ahch.datadialog.net, cloud.ahch.datadialog.net, pad.ahch.datadialog.net
    - backup and logrotate cron jobs
    - create and link custom-addons githup repository into the instance addons folder
    - Install push-to-deploy workflow for updating the custom addons folder
- **maintenancemode** (DEPRICATED by Saltstack) set one or all instances into maintenance mode (not reachable from the outside)
- **backup** one or all instances
- **restore** one or all instances

**HINT:** **db-tools.sh** is used by odoo-tools.sh to backup and restore the database and data-dir of an instance.

## DEVELOPMENT
Development is all done locally on mac or linux machines with pycharm.

#### Development workflow:
```bash
# 1.) Clone the branch o8 locally:
git clone -b o8 https://github.com/OpenAT/online
git submodule update --init --recursive
git branch -avv

# 2.) Create and checkout a new branch:
#     Optional Create a new Issue in Github First for the issue number
git branch o8_ckeditor_advanced
git checkout o8_ckeditor_advanced

# 3.) Push your Branch to Github (so everybody knows what you are working on)
git commit
git push origin o8_ckeditor_advanced

# 4.) Do stuff and commit and push changes until ready:
git add [file or folders]    # This tells git what to include in next commit
git commit -m "[ADD] Added README.md"
git push origin o8_ckeditor_advanced

# 5.) Merging the Branch
# 5.1) Update master branch first
git fetch
git checkout o8
git pull
# 5.2) Rebase development branch on master branch (o8) to add possible changes, avoiding merge confilcts later on!
git checkout o8_ckeditor_advanced
git rebase o8
git submodule update
# 5.3) Locally merge the Development Branch (o8_ckeditor_advanced) into the master branch (o8)
#      !!! OR Create a Pull request in Github which is the prefered method !!!
git checkout o8
git merge o8_ckeditor_advanced
git push origin master
```

#### Adding new Submodules to the repo:
```bash
# This is an example how to add a submodule with the submodule branch master:
git submodule add -b master https://github.com/ether/etherpad-lite.git etherpad-lite

# Update all submodules
git submodule update --rebase --remote --recursive
```

#### Update of all existing Submodules
```bash
git checkout o8
git pull
git submodule update --remote --rebase --recursive
git commit -am "[UPDATE] all submodules updated"
git push origin o8
```

## DOCUMENTATION

#### odoo v8
- [Latest Dev Docu](https://www.odoo.com/documentation/master/howtos/website.html)
- [odoo v8 api guidelines](http://odoo-new-api-guide-line.readthedocs.org/en/latest/)
- [Technical Memento](https://www.odoo.com/files/memento/OpenERP_Technical_Memento_latest.pdf)
- [eval many2many write](https://doc.odoo.com/v6.0/developer/2_5_Objects_Fields_Methods/methods.html/#osv.osv.osv.write)
- [WebApps Tutorial HBEE](https://www.hbee.eu/en-us/blog/archive/2014/9/17/odoo-web-apps/)
- [Forum how to's](https://www.odoo.com/forum/how-to)

#### Configuration (res.config) related
- https://www.odoo.com/forum/help-1/question/how-can-i-save-load-my-own-configuration-settings-30123
- https://www.odoo.com/forum/help-1/question/how-can-i-create-own-config-for-my-custom-module-41981
- https://www.odoo.com/forum/help-1/question/is-it-possible-to-set-database-default-configuration-values-507
- https://doc.odoo.com/6.0/developer/5_16_data_serialization/xml_serialization/
- http://stackoverflow.com/questions/9377402/insert-into-many-to-many-openerp/9387447#9387447

#### Other odoo Tools and Docs
- [carddav for odoo](https://github.com/initOS/openerp-dav)
- http://odoohub.wordpress.com/2014/08/15/where-is-the-odoo-documentation/
- http://djpatelblog.blogspot.in/2014/09/odoo-new-api-recordsets.html
- [server.conf db_filter= parameter](https://www.odoo.com/forum/help-1/question/domain-based-db-filter-6583)

#### XMLRPC, ErpPeek, Connector ...
- [XMLRPC and erppeek by wirtel](http://wirtel.be/posts/en/2014/06/13/using_erppeek_to_discuss_with_openerp/)
- [erppeek](http://erppeek.readthedocs.org/en/latest/index.html)
- [oerplib](https://github.com/osiell/oerplib)
- [oerlib docu](https://pythonhosted.org/OERPLib/#supported-openerp-odoo-server-versions)
- [xmlrpc lib docu](https://docs.python.org/2/library/xmlrpclib.html)
- [odoo connector](http://odoo-connector.com)

#### git, git workflow and github
- [Github Rebase Workflow](http://mettadore.com/2011/09/07/the-ever-deployable-github-workflow/)
- [Git Submodules](http://git-scm.com/docs/git-submodule)
- [Github Using Pull Requests](https://help.github.com/articles/using-pull-requests/)
- [Adding an existing project to github](https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/)
- [Push to a Remote](https://help.github.com/articles/pushing-to-a-remote/)
- [README.md Markdown Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

#### Odoo Setup in Ubuntu 14.04 LTS
- [nginx and odoo](http://wirtel.be/posts/en/2011/11/02/nginx-proxy-openerp/)
- [odoo v7 setup scripts](https://github.com/OpenAT/odoo-tools/tree/7.0)
- [odoo 8 setup script by Andre Schenkel](https://github.com/lukebranch/odoo-install-scripts/blob/master/odoo-saas4/ubuntu-14-04/odoo_install.sh)
- [odoo setup ubuntu 14 lts](https://www.odoo.com/forum/help-1/question/how-to-install-odoo-from-github-on-ubuntu-14-04-for-testing-purposes-only-ie-not-for-production-52627)

#### Python, PIP, VirtualEnv
- [PYTHON](https://www.python.org)
- [Python Quick Ref](http://rgruet.free.fr/#QuickRef)
- [PIP Docu](http://pip.readthedocs.org/en/latest/user_guide.html#requirements-files)
- [argparse](https://docs.python.org/2.7/library/argparse.html#other-utilities)

#### BASH Scripting
- [if conditions](http://www.tldp.org/LDP/Bash-Beginners-Guide/html/sect_07_01.html)
- [sed](http://wiki.ubuntuusers.de/sed)

#### Java Script
- https://developer.mozilla.org/de/docs/Web/JavaScript
