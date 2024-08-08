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

Since its inception this library was extended with a few useful helper functions and specialized logging classes.


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


ForwardingLogger
--------------------------------

This logger forwards messages above a certain level (by default: all messages) to a configured parent logger. Optionally it can prepend the configured `forward_prefix` to all *forwarded* log messages. `forward_suffix` works like `forward_prefix` but appends some string.

This can be helpful if you need to log contextualized messages. For example you could log detailed messages related to a specific file in "imgfile.log" but you want more important messages (e.g. warnings, errors) in another log file used by your application. In that scenario you can quickly spot problems in your main log file while detailed data is available in separate log files.

Python's default logging module can not handle this because:

- A `Logger`'s log level is only applied for messages emitted directly on that logger (not for propagated log messages), see this [blog post by Marius Gedminas](https://mg.pov.lt/blog/logging-levels.html).
- Adding a log prefix only for certain loggers can only by done by duplicating handler configuration. Python's handlers are quite basic so if the duplicated handlers access a shared resource (e.g. a log file) Python will open it twice (which causes data loss if `mode='w'` is used).

**Usage:**

```python
import logging
from schwarz.log_utils import get_logger, ForwardingLogger

parent_logger = logging.getLogger('foo')
log = ForwardingLogger(
    forward_to=parent_logger,
    forward_prefix='[ABC] ',
    forward_minlevel=logging.INFO
)
log.info('foo')
# parent_logger sees a log message like "[ABC] foo"
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
# this raises an AssertionError as "foo" was logged with INFO
assert_did_log_message(lc, 'foo', level=logging.DEBUG)

lr = assert_did_log_message(lc, 'foo', level=logging.INFO)
# you can also inspect the actual "LogRecord" instance "lr" if you need to

assert_no_log_messages(lc, min_level=logging.WARN)
```


Changes
--------------------------------

**0.7.0** (2024-08-06)

- drop support for Python 2


**0.6.2** (2022-05-25)

- `assert_did_log_message(…)` now returns the `LogRecord` instance which can
   be used by the caller for more detailled checks.
- `ForwardingLogger` now also forwards `.exc_info` correctly so that the main
   logger can also log exceptions.

