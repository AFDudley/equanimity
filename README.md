# Equanimity

Equanimity is a world building game with a heavy emphasis on squad-based turn-based combat and balance.

## Installation

From inside cloned repo:

> $ git checkout dev-docker

> $ docker build -t aequalis .

> $ docker run -p 8080:8080 aequalis

If you haven't already, you'll need to NAT the port in order to connect:

> $ VBoxManage controlvm <name of your docker-machine env here> natpf1 "aequalis,tcp,127.0.0.1,8080,,8080"

Then with a web browser navigate to 127.0.0.1:8080 (currently this is address is baked in.)

If everything is configured correct a page should appear.

Finally, run demo:

> $ tools/demo.py --url=http://127.0.0.1:8080

Currently, the demo does not always exit cleanly, but if everything is configured correctly it will work.

##Running tests
From inside virtualenv
> $ ./setup.py test [--nose-only] [--run-failed]

Coverage statements should print to the terminal when running the tests.
--nose-only indicates to run only the nose test runner, and not the pep8 and pyflakes checkers
--run-failed passes this option to nose, which will only re-run failed tests
