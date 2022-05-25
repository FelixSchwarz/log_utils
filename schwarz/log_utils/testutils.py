# -*- coding: utf-8 -*-
# Copyright (c) 2020-2022 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

import logging

from . import log_proxy
from .log_proxy import CollectingHandler


__all__ = [
    'assert_did_log_message',
    'assert_no_log_messages',
    'build_collecting_logger',
    'LogHelper',
]

def assert_did_log_message(log_capture, expected_msg, level=None):
    lc = log_capture
    if not lc.records:
        raise AssertionError('no messages logged')

    for log_record in lc.records:
        logged_msg = log_record.getMessage()
        if logged_msg == expected_msg:
            if (level is not None) and (log_record.levelno != level):
                raise AssertionError('expected log level %s but logged message has %s: %s' % (level, log_record.levelno, expected_msg))
            # returning the log record is helpful so that the caller can
            # inspect the logged data in detail (e.g. check ".exc_info").
            return log_record

    log_messages = [lr.getMessage() for lr in lc.records]
    raise AssertionError('message not logged: "%s" - did log %s' % (expected_msg, log_messages))

def assert_no_log_messages(log_capture, min_level=None):
    lc = log_capture
    log_records = lc.records
    if (min_level is None) and not log_records:
        return
    elif min_level is not None:
        log_records = [lr for lr in lc.records if (lr.levelno >= min_level)]
        if not log_records:
            return
    log_messages = [log_record.getMessage() for log_record in log_records]
    raise AssertionError('unexpected log messages: %s' % log_messages)


def build_collecting_logger(logger_name='collecting_logger'):
    log = logging.Logger(logger_name)
    ch = CollectingHandler(flush_level=logging.CRITICAL)
    log.addHandler(ch)
    # workaround so that other helper functions can treat the handler like a
    # LogCapture instance
    ch.records = ch.buffer
    return log, ch



class LogHelper(object):
    """Crude helper to avoid cross-test pollution.

    Python's logging module keeps a global registry and somehow I got test
    failures after adding a second test case which used LogCapture().
        Symptom: LogCapture() did not capture any log messages in some tests

    I hoped that LogCapture() would somehow clean up all global references but
    it did not. Quick fix is to manually do some monkey patching and remove
    loggers from the global registry afterwards.
    """
    def __init__(self):
        self._loggers = set()
        self._initial_function = None
        self._globals = None

    @classmethod
    def set_up(cls, test=None, globals_=None):
        helper = LogHelper()
        helper.activate(globals_=globals_)
        if test:
            test.addCleanup(helper.cleanup)
        return helper

    def activate(self, globals_=None):
        if globals_:
            self._initial_function = globals_['get_logger']
            globals_['get_logger'] = self.get_logger
            self._globals = globals_
        log_proxy.get_logger = self.get_logger

    def get_logger(self, *logger_args, **logger_kwargs):
        logger = self._initial_function(*logger_args, **logger_kwargs)
        self._loggers.add(logger.name)
        return logger

    def cleanup(self):
        log_proxy.get_logger = self._initial_function
        if self._initial_function and self._globals:
            self._globals['get_logger'] = self._initial_function
        manager = logging.Logger.manager
        for logger_name in self._loggers:
            manager.loggerDict.pop(logger_name, None)
        self._loggers = set()

