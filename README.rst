************
Layer Export
************

.. contents::

Prerequisites
=============

Python >= 2.7, PIP, Git, VirtualEnv (mkvirtualenv helper script)


Getting Started
===============

Preparing virtualenv paths (optional if your profile doesn't have it).
::
    export WORKON_HOME=~/Envs
    source /usr/local/bin/virtualenvwrapper_lazy.sh


Start by creating a virtual environment using the helper scripts provided. Do not include the systems site-packages.
::
    mkvirtualenv layer-export --no-site-packages
    workon layer-export


Clone the Github repository if you have not done so yet. You will need a git account to do this.
::

    git clone git@github.com:ArabellaTech/layer-export.git

Move into the newly created layer-export folder.

Install the Python requirements using PIP, which are located in the requirements.txt file.::

    pip install -r requirements.txt


Running
=======

Request export (once per 24h)::

    python layer-export.py --app-id production/XXXX --token YYYY


Update `decrypt.sh` and run::

    sh decrypt.sh
