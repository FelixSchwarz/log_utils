schwarzlog
=======================

Library to add some missing functionality in Python's `logging` module.

    $ pip install schwarzlog

Caveat: Most functionality is currently not documented. I'll to write some docs going forward, though.


Motivation / Background
--------------------------------

logging is often helpful to find problems in deployed code.

However Python's logging infrastructure is a bit annoying at times. For example if a library starts logging data but the application/unit test did not configure the logging infrastructure Python will emit warnings. If the library supports conditional logging (e.g. passing a flag if it should use logging to avoid the "no logging handler installed" issue mentioned above) this might complicate the library code (due to "is logging enabled" checks).

Also I find it a bit cumbersome to test Python's logging in libraries because one has to install global handlers (and clean up when the test is done!).

This library should solve all these problems with a helper function:

- It can just return a new logger with a specified name.
- If logging should be disabled entirely it just returns a fake logger which will discard all messages. The application doesn't have to be aware of this and no global state will be changed.
- The caller can also pass a pre-configured logger (e.g. to test the emitted log messages easily or to use customized logging mechanisms).


CallbackLogger
--------------------------------

A `Logger`-like class which can trigger a additional callback in addition to passing a log message through the logging infrastructure. I'm using this to ensure severe problems logged by lower-level libraries will be displayed in the UI. If you set `merge_arguments = True` the callback only gets the final message (as `str`), otherwise it'll get the `logging.LogRecord`.

**Usage:**

```python
import logging
from schwarz.log_utils import CallbackLogger

_l = logging.getLogger('foo')
logged_msgs = []
cb = logged_msgs.append
log = CallbackLogger(log=_l, callback=cb, callback_minlevel=logging.ERROR, merge_arguments=True)
log.info('info message')
log.error('error message')
logged_msgs == ['error message']
```


Support for writing tests
--------------------------------

The library also contains some helpers to ease writing logging-related tests.

```python
import logging
from schwarz.log_utils.testutils import *

# "lc" works a bit similar to a LogCapture instance
log, lc = build_collecting_logger()
log.info('foo')
log.debug('bar')

assert_did_log_message(lc, 'foo')
assert_did_log_message(lc, 'foo', level=logging.INFO)
# this raises an AssertionError as "foo" was logged with INFO
assert_did_log_message(lc, 'foo', level=logging.DEBUG)
assert_no_log_messages(lc, min_level=logging.WARN)
```

