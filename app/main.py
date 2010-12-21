import sys
import os.path
import logging
# add src directory to sys path.
DIR_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
sys.path = [os.path.join(DIR_PATH, 'src')] + sys.path

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app



from birdtoword import page, api, fb

handlers = []

for module in (page, api, fb):
    for item in vars(module).values():
        if isinstance(item, object) and hasattr(item, 'url'):
            handlers.append((item.url, item))

logging.info("Found the following handlers: %r" % handlers)
application = webapp.WSGIApplication(
    handlers,
    debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
