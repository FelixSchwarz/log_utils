# -*- coding: utf-8 -*-
# Copyright (c) 2017, 2019, 2022 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging
import sys


__all__ = ['contextfile_logger', 'ForwardingLogger']

class ForwardingLogger(logging.Logger):
    """
    This logger forwards messages above a certain level (by default: all messages)
    to a configured parent logger. Optionally it can prepend the configured
    "forward_prefix" to all *forwarded* log messages.
    "forward_suffix" works like "forward_prefix" but appends some string.

    Python's default logging module can not handle this because
      a) a logger's log level is only applied for messages emitted directly on
         that logger (not for propagated log messages), see
         https://mg.pov.lt/blog/logging-levels.html
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
            record_kwargs = {
                'exc_info': record.exc_info,
            }
            if hasattr(record, 'stack_info'):
                # Python 3
                record_kwargs['stack_info'] = record.stack_info
            self._forward_to.log(record.levelno, msg, *record.args, **record_kwargs)

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
