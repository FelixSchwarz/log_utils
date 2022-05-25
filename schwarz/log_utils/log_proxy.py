# -*- coding: utf-8 -*-
# Copyright (c) 2013-2017, 2019 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT
"""
logging is often helpful to find problems in deployed code.

However Python's logging infrastructure is a bit annoying at times. For example
if a library starts logging data but the application/unit test did not configure
the logging infrastructure Python will emit warnings.

If the library supports conditional logging (e.g. passing a flag if it should
use logging to avoid the "no logging handler installed" issue mentioned above)
this might complicate the library code (due to "is logging enabled" checks).

Also I find it a bit cumbersome to test Python's logging in libraries because
one has to install global handlers (and clean up when the test is done!).

This library should solve all these problems with a helper function:
- It can just return a new logger with a specified name.
- If logging should be disabled entirely it just returns a fake logger which
  will discard all messages. The application doesn't have to be aware of this
  and no global state will be changed.
- The caller can also pass a pre-configured logger (e.g. to test the emitted
  log messages easily or to use customized logging mechanisms).
"""

import logging
from logging.handlers import MemoryHandler


__all__ = [
    'get_logger', 'l_', 'log_',
    'CollectingHandler',
    'NullLogger',
]

# This is added for backwards-compatibility with Python 2.6
class NullLogger(logging.Logger):
    def _log(self, *args, **kwargs):
        pass

    def handle(self, record):
        pass


class CollectingHandler(MemoryHandler):
    """
    This handler collects log messages until the buffering capacity is
    exhausted or a message equal/above a certain level was logged. After the
    first (automatic) flush buffering is disabled (manual calls to .flush()
    do not disable buffering).
    Flushing only works if a target was set.
    """
    def __init__(self, capacity=10000, flush_level=logging.ERROR, target=None):
        super(CollectingHandler, self).__init__(capacity, flushLevel=flush_level, target=target)

    def shouldFlush(self, record):
        should_flush = super(CollectingHandler, self).shouldFlush(record)
        if should_flush and self.capacity > 0:
            # disable buffering after the first flush was necessary...
            self.capacity = 0
        return should_flush

    def set_target(self, target, disable_buffering=False):
        self.target = target
        if disable_buffering:
            self.capacity = 0
            self.flush()
    setTarget = set_target


class ContextAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if not self.extra:
            return (msg, kwargs)
        extra_data = tuple(self.extra.items())
        assert len(extra_data) == 1
        ctx_value = extra_data[0][1]
        adapted_msg = '[%s] %s' % (ctx_value, msg)
        return (adapted_msg, kwargs)


def get_logger(name, log=True, context=None, level=None):
    if not log:
        log = NullLogger('__log_proxy')
    elif not isinstance(log, logging.Logger):
        log = logging.getLogger(name)
    if level is not None:
        log.setLevel(level)
    if context is None:
        return log
    adapter = ContextAdapter(log, {'context': context})
    return adapter


def log_(name, get_logger_=None):
    """Return a Logger for the specified name. If get_logger is None, use
    Python's default getLogger.
    """
    get_func = get_logger_ if (get_logger_ is not None) else logging.getLogger
    return get_func(name)

def l_(log, fallback=None):
    """Return a NullLogger if log is None.

    This is useful if logging should only happen to optional loggers passed
    from callers and you don't want clutter the code with "if log is not None"
    conditions."""
    if log is None:
        return NullLogger('__log_proxy') if (fallback is None) else fallback
    return log
