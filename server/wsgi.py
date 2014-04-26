import sys
import logging
from server import create_app

# log to wsgi files
logging.basicConfig(stream=sys.stderr)
# capture print statements instead of crashing wsgi
sys.stdout = sys.stderr

application = create_app(config='production')
application = create_app(config='dev')
