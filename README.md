This project thrives to integrate the [shotgun toolkit](https://toolkit.shotgunsoftware.com/home) with facilities of [bcore](https://github.com/Byron/bcore).

For that reason, whenever *tank* is supposed to be used, *btank* is used to initialize it. That way, monkey patches can be applied as necessary.

## Requirements

* [shotgun toolkit](https://github.com/shotgunsoftware/tk-core)
* [shotgun events](https://github.com/Byron/shotgun-events)
    - for test-suite only

## Development Status

[![Coverage Status](https://coveralls.io/repos/Byron/btank/badge.png)](https://coveralls.io/r/Byron/btank)
[![Build Status](https://travis-ci.org/Byron/btank.svg?branch=master)](https://travis-ci.org/Byron/btank)
![under construction](https://raw.githubusercontent.com/Byron/bcore/master/src/images/wip.png)

## Running Tests

```bash
# assure virtualenv exists and bootstrap everything there.
# Can be called safely without redoing any work 
source ./bin/venv.env
nosetests src/python/btank/tests
```

##  Credits

* [python-patch](https://code.google.com/p/python-patch)
