# Equanimity

Equanimity is a world building game with a heavy emphasis on squad-based turn-based combat and balance.

## Installation

First, create a virtualenv, clone the repository into the env, cd into repo.

Then, install dependencies:

> $ pip install -r requirements.txt

Then, make directories:

> $ mkdir logs

> $ mkdir -p DBs/World

Start ZODB instance:

> $ runzeo -C zeo/zeoWorld.conf &

Next, create world:

> $ tools/init._db.py

Run wsgi server:

> $ ./run_wsgi_server.sh

Start redis

Start celery worker:
> $ celery -A worker.world_tasks worker

Finally, run demo:

> $ tools/demo.py --url=http://127.0.0.1:8080

##Running tests
From inside virtualenv
> $ ./setup.py test [--nose-only] [--run-failed]

Coverage statements should print to the terminal when running the tests.
--nose-only indicates to run only the nose test runner, and not the pep8 and pyflakes checkers
--run-failed passes this option to nose, which will only re-run failed tests
