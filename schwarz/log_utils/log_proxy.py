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
import sys


__all__ = [
    'contextfile_logger', 'get_logger', 'l_', 'log_', 'ForwardingLogger',
    'CollectingHandler',
    'NullLogger',
]

# This is added for backwards-compatibility with Python 2.6
class NullLogger(logging.Logger):
    def _log(self, *args, **kwargs):
        pass

    def handle(self, record):
        pass


class ForwardingLogger(logging.Logger):
    """
    This logger forwards messages above a certain level (by default: all messages)
    to a configured parent logger. Optionally it can prepend the configured
    "forward_prefix" to all *forwarded* log messages.
    "forward_suffix" works like "forward_prefix" but appends some string.

    Python's default logging module can not handle this because
      a) a logger's log level is only applied for messages emitted directly on
         that logger (not for propagated log messages), see
         http://mg.pov.lt/blog/logging-levels.html
      b) adding a log prefix only for certain loggers can only by done by
         duplicating handler configuration. Python's handlers are quite basic
         so if the duplicated handlers access a shared resource (e.g. a log file)
         Python will open it twice (which causes data loss if mode='w' is
         used).
      c) and last but not least we often need to configure the specific logging
         handlers dynamically (e.g. log to a context-dependent file) which is
         not doable via Python's fileConfig either - so we can go fully dynamic
         here...
    """
    def __init__(self, *args, **kwargs):
        self._forward_to = kwargs.pop('forward_to')
        self._forward_prefix = kwargs.pop('forward_prefix', None)
        self._forward_suffix = kwargs.pop('forward_suffix', None)
        self._forward_minlevel = kwargs.pop('forward_minlevel', logging.NOTSET)
        if (not args) and ('name' not in kwargs):
            name = self.__class__.__name__
            args = (name, )
        super(ForwardingLogger, self).__init__(*args, **kwargs)

    def callHandlers(self, record):
        nr_handlers = self._call_handlers(record)
        if self._forward_to is None:
            self._emit_last_resort_message(record, nr_handlers)

        # "logging.NOTSET" (default) is defined as 0 so that works here just fine
        if (record.levelno >= self._forward_minlevel) and (self._forward_to is not None):
            msg = record.msg
            if self._forward_prefix:
                msg = self._forward_prefix + msg
            if self._forward_suffix:
                msg += self._forward_suffix
            self._forward_to.log(record.levelno, msg, *record.args)

    def _call_handlers(self, record):
        # ,--- mostly copied from logging.Logger.callHandlers -----------------
        logger = self
        nr_found = 0
        while logger:
            for handler in logger.handlers:
                nr_found = nr_found + 1
                if record.levelno >= handler.level:
                    handler.handle(record)
            if logger.propagate:
                logger = logger.parent
            else:
                break
        return nr_found
        # `--- end copy -------------------------------------------------------

    def _emit_last_resort_message(self, record, nr_handlers):
        # ,--- mostly copied from logging.Logger.callHandlers -----------------
        if nr_handlers > 0:
            return
        if logging.lastResort:
            if record.levelno >= logging.lastResort.level:
                logging.lastResort.handle(record)
        elif logging.raiseExceptions and not self.manager.emittedNoHandlerWarning:
            sys.stderr.write("No handlers could be found for logger"
                             " \"%s\"\n" % self.name)
            self.manager.emittedNoHandlerWarning = True
        # `--- end copy -------------------------------------------------------



def contextfile_logger(logger_name, log_path=None, handler=None, **kwargs):
    """
    Return a ForwardingLogger which logs to the given logfile.

    This is a generic example how to use the ForwardingLogger and can be used
    to create log files which are placed near the data they are referring to.
    """
    log = ForwardingLogger(logger_name,
        forward_to=kwargs.pop('forward_to', None),
        forward_prefix=kwargs.pop('forward_prefix', None),
        forward_minlevel=kwargs.pop('forward_minlevel', logging.NOTSET),
        **kwargs
    )
    if handler is None:
        # The logging module does not keep a reference to this FileHandler anywhere
        # as we are instantiating it directly (not by name or fileconfig).
        # That means Python's garbage collection will work just fine and the
        # underlying log file will be closed when our batch-specific
        # ForwardingLogger goes out of scope.
        handler = logging.FileHandler(log_path, delay=True)
        handler.setFormatter(logging.Formatter(
            fmt='%(asctime)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
    log.addHandler(handler)
    return log


class CollectingHandler(MemoryHandler):
    """
    This handler collects log messages until the buffering capacity is
    exhausted or a message equal/above a certain level was logged. After the
    first (automatic) flush buffering is disabled (manual calls to .flush()
    do not disable buffering).
    Flushing only works if a target was set.
    """
    def __init__(self, capacity=10000, flush_level=logging.ERROR, target=None):
        super().__init__(capacity, flushLevel=flush_level, target=target)

    def shouldFlush(self, record):
        should_flush = super().shouldFlush(record)
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
