import urllib2
import os
import shutil
import sys

from paver.easy import *
from paver.path import path
import paver.doctools
from paver.setuputils import setup

options(
    virtualenv=dict(
        script_name="bootstrap.py",
        paver_command_line="init",
        ))

def cmd(c, silent=False):
    if not silent:
        print c
    os.system(c)

def download(url, filepath=None):
    if filepath is None:
        filepath = url.split('/')[-1]
    print "downloading %s to %s" % (url, filepath)
    open(filepath,'w').write(urllib2.urlopen(url).read())

def unzip(path):
    cmd("unzip -uq %s" % path)

@task
def getappengine():
    """Download Google App Engine"""
    if os.path.exists("google_appengine_1.4.0.zip"):
        cmd("rm google_appengine_1.4.0.zip")
    if os.path.isdir("google_appengine"):
        cmd("rm -rf google_appengine")
    open("google_appengine_1.4.0.zip","w").write(urllib2.urlopen("http://googleappengine.googlecode.com/files/google_appengine_1.4.0.zip").read())
    cmd("unzip -uq google_appengine_1.4.0.zip")
    cmd("rm google_appengine_1.4.0.zip")

@task
def init():
    """Initialize everything so you can start working"""
    getappengine()

@task
def buildbuckets():
    cmd("cd app && python build.py -o paths -s 3 -m 8")

@task
def run():
    """Run the google app engine development server against gvr-online"""
    cmd("google_appengine/dev_appserver.py --enable_sendmail --address=0.0.0.0 app")


@task
def deploy():
    """Deploy to google app engine."""
    cmd("google_appengine/appcfg.py update app")
