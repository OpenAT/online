# odoo_v8.0
This repo is used for production for odoo v8 installations. It is also the place where we develop our own addons for
odoo. The *master* branch of this repo is alway the deployable production ready branch. All branch names uploaded here
have to follow this rules:

- DEVELOPMENT: dev-[module name OR feature name] e.g.: *dev-ckeditor_advanced*
- FIXES: fix-[ISSUE Number] e.g.: *fix-1234* - Because of this there has to be an github Issue first!
- CUSTOMER: cus-[customer id] e.g.: *cus_hof*

Customer specific developments and fixes work like *cus_hof-dev-ckeditor_advanced* OR *cus_hof-fix-3425*

## Features

### Better version and update handling
- updated requirements.txt to install with pip install -r /path/to/requirements.txt
- all third party addons as well as odoo itself are linked as submodules

### Planned: Simple setup through setup-tools.sh
setup-tools.sh will be a simple setup script that is able to 
- setup new instances of odoo on the local server
- deploy addon(s) to one or more databases on the local server
- backup and restore databases (and data-dir) on the local server

## SETUP
Right now the Setup process is still done manualy - but in the ner future setup-tools.sh will handls everything. As
soon as this script is finished it will be documented here.

You could find some guidance for the setup script here:
- [odoo v7 setup scripts]
- 
-

## DEVELOPMENT

To use this branch for development use this workflow:

```bash
# Clone the repo odoo_v8 branch master locally:
git clone -b master --depth 1 --single-branch --recurse-submodules https://github.com/OpenAT/odoo_v8.0.git [instance_dir]

# Check if the upstream (remote) is set correctly for the master branch
git branch -vv # or
git branch -a
git --set-upstream-to=https://github.com/OpenAT/odoo_v8.0.git master

# Create and checkout a new branch:
git branch dev-ckeditor_advanced
git checkout dev-ckeditor_advanced

# Push your Branch to Github (so everybody knows what you are working on)
#maybe: git commit -m "[NEW] New Branch added for customer HOF"
git push origin dev-ckeditor_advanced

# Do stuff and commit changes:
git add [file or folders] # This tells git what to include in next commit
git commit -m "[IMP] Added README.md"
git push origin dev-ckeditor_advanced

# When ready with development rebase and integrate into master
git fetch origin/master
git rebase 


```

### Create a local branch for development
```bash
# Create a new branch
git branch dev-base_config
# Checkout the new branch
git checkout dev-base_config
```

ToDo: WAY MORE description of how to develop with git and how to use this repo in production!

## Documentation

### odoo v8
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
- http://erppeek.readthedocs.org/en/latest/index.html
- http://odoohub.wordpress.com/2014/08/15/where-is-the-odoo-documentation/
- http://djpatelblog.blogspot.in/2014/09/odoo-new-api-recordsets.html
- http://wirtel.be/posts/en/2011/11/02/nginx-proxy-openerp/


### github docu
- [Adding an existing project to github](https://help.github.com/articles/adding-an-existing-project-to-github-using-the-command-line/)
- [Push to a Remote](https://help.github.com/articles/pushing-to-a-remote/)
- [README.md Markdown Cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)