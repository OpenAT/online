# -*- coding: utf-'8' "-*-"
import sys
import os
from os.path import join as pj

# HINT: This is not overly "eloquently" written because it will not search for folder locations ;)
# ----- START MAIN ROUTINE -----
if __name__ == "__main__":
    script_path = os.path.dirname(sys.argv[0])
    base_path = os.path.dirname(script_path)  # cd..
    target_path = pj(script_path, 'openerp/addons')

    odoo_root_addons_path = pj(base_path, 'odoo/openerp/addons')
    odoo_addons_path = pj(base_path, 'odoo/addons')
    loaded_addons_path = pj(base_path, 'addons-loaded')

    # Check that the path exists
    for path in [target_path, odoo_root_addons_path, odoo_addons_path, loaded_addons_path]:
        assert os.path.exists(path), 'ERROR: path missing: %s' % path

    # Change the current path to the target path
    os.chdir(target_path)

    # Find paths for odoo/addons and addons_loaded relative to the target_path
    rel_addon_paths = []
    for path in [odoo_root_addons_path, odoo_addons_path, loaded_addons_path]:
        #List files in addon path
        for addon in os.listdir(path):
            addon_abspath = pj(path, addon)
            # Limit results to folders and symlinks pointing to folders only
            if os.path.isdir(addon_abspath):
                # Symlinks
                if os.path.islink(addon_abspath):
                    # Get the absolute path for any symlink
                    addon_abspath = pj(os.path.dirname(addon_abspath), os.readlink(addon_abspath))
                # Store the relative path to the addon
                rel_addon_paths.append(os.path.relpath(addon_abspath, target_path))

    print "rel_addon_paths: %s" % rel_addon_paths

    # Remove existing addon-symlinks
    print "Removing existing symlinks"
    del_symlinks = [os.remove(pj(target_path, f))
                    for f in os.listdir(target_path)
                    if os.path.isdir(pj(target_path, f)) and os.path.islink(pj(target_path, f))]

    # Create new addon-symlinks
    print "Creating symlinks for addons"
    os.chdir(target_path)
    for addon in rel_addon_paths:
        os.symlink(addon, os.path.basename(addon))

    print "Create symlinks for files and folders in odoo/openerp/* (excluding odoo/openerp/addons and .pyc files)"
    openerp_folder = pj(base_path, 'odoo/openerp')
    os.chdir(pj(base_path, 'devel/openerp'))
    for f in os.listdir(openerp_folder):
        if f != 'addons' and os.path.splitext(f)[1] != '.pyc':
            # Get the absolute path for the file
            abspath = pj(openerp_folder, f)
            relpath = os.path.relpath(abspath, pj(script_path, 'openerp'))
            os.symlink(relpath, os.path.basename(relpath))
            #print "ln -s %s %s" % (relpath, os.path.basename(relpath))
