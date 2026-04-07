# -*- coding: utf-8 -*-
__revision__ = "$Id: $"

import sys
import os
from os.path import join as pj

from setuptools import setup, find_namespace_packages

versioninfo = {}
p3ddir = pj(os.path.dirname(__file__),'src', 'openalea', 'plantscan3d')
with open(pj(p3ddir,"__version__.py")) as fp:
    exec(fp.read(), versioninfo)

globals().update(versioninfo)

# Packages list, namespace and root directory of packages

pkg_root_dir = 'src'
pkgs = [ pkg for pkg in find_namespace_packages(pkg_root_dir)]


setup(
    name=name,
    version=version,
    description=description,
    long_description=long_description,
    author=authors,
    author_email=authors_email,
    url=url,
    license=license,
    keywords = '',	

    # package installation
    packages= pkgs,	
    package_dir = {
        '' : 'src'
    },

    # Namespace packages creation by deploy
    #namespace_packages = ['openalea'],
    #create_namespaces = False,
    zip_safe= False,

    # Eventually include data in your package
    # (flowing is to include all versioned files other than .py)
    include_package_data = True,
    # (you can provide an exclusion dictionary named exclude_package_data to remove parasites).
    # alternatively to global inclusion, list the file to include   
    package_data = {'' : ['*.ui', '*.rc', '*.qrc','*.conf','*.png'],},

    # postinstall_scripts = ['',],

    # Declare scripts and wralea as entry_points (extensions) of your package 
    entry_points = { 
        'wralea' : ['plantscan3d = openalea.plantscan3d_wralea' ],
        #'console_scripts': [
        #       'fake_script = openalea.fakepackage.amodule:console_script', ],
        'gui_scripts': [
              'plantscan3d = openalea.plantscan3d.main_window:main',],
        #	'wralea': wralea_entry_points
        },
    )


