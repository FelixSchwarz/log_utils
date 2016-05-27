# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
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

__all__ = ['get_logger', 'l_', 'log_']

class NullLogger(logging.Logger):
    def _log(self, *args, **kwargs):
        pass

    def handle(self, record):
        pass


def get_logger(name, log=True):
    if isinstance(log, logging.Logger):
        return log
    elif log:
        return logging.getLogger(name)

    fake_logger = NullLogger('__log_proxy')
    return fake_logger

def log_(name, get_logger_=None):
    """Return a Logger for the specified name. If get_logger is None, use
    Python's default getLogger.
    """
    get_func = get_logger_ if (get_logger_ is not None) else logging.getLogger
    return get_func(name)

def l_(log):
    """Return a NullLogger if log is None.

    This is useful if logging should only happen to optional loggers passed
    from callers and you don't want clutter the code with "if log is not None"
    conditions."""
    if log is None:
        return NullLogger('__log_proxy')
    return log
