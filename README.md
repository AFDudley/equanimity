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

> $ python tools/create_world.py

Finally, run pyramid server:

> $ python server.py
 
