# -*- coding: utf-8 -*-
# Copyright (c) 2019 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from pythonic_testcase import *
from testfixtures import LogCapture

from .. import log_proxy
from ..log_proxy import get_logger, CollectingHandler, ForwardingLogger


class ForwardingLoggerTest(PythonicTestCase):
    def setUp(self):
        self.log_helper = LogHelper.set_up(test=self)

    def test_can_forward_with_prefix(self):
        with LogCapture() as l_:
            log = get_logger('bar')
            wrapped_log = ForwardingLogger(forward_to=log, forward_prefix='[ABC] ', forward_minlevel=logging.INFO)
            wrapped_log.info('hello world')
            wrapped_log.debug('should be ignored')
        l_.check(('bar', 'INFO', '[ABC] hello world'),)

    def test_can_forward_with_suffix(self):
        with LogCapture() as l_:
            log = get_logger('bar')
            wrapped_log = ForwardingLogger(forward_to=log, forward_suffix=' (foo)')
            wrapped_log.info('hello world')
        l_.check(('bar', 'INFO', 'hello world (foo)'),)

    def test_no_output_to_lastresort_if_contains_forwarding_logger(self):
        with LogCapture() as l_:
            log = get_logger('bar')
            wrapped_log = ForwardingLogger(forward_to=log, forward_suffix=' (foo)')
            assert_is_empty(wrapped_log.handlers)
            wrapped_log.info('hello world')
        l_.check(('bar', 'INFO', 'hello world (foo)'),)
        assert_is_empty(self.log_helper.unclaimed_logs.buffer,
            message='user might see output on STDERR')



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
        self._last_resort = None
        self.unclaimed_logs = CollectingHandler()

    @classmethod
    def set_up(cls, test=None):
        helper = LogHelper()
        helper.activate()
        if test:
            test.addCleanup(helper.cleanup)
        return helper

    def activate(self):
        self._initial_function = globals()['get_logger']
        log_proxy.get_logger = self.get_logger
        globals()['get_logger'] = self.get_logger
        self._last_resort = logging.lastResort
        logging.lastResort = self.unclaimed_logs

    def get_logger(self, *logger_args, **logger_kwargs):
        logger = self._initial_function(*logger_args, **logger_kwargs)
        self._loggers.add(logger.name)
        return logger

    def cleanup(self):
        log_proxy.get_logger = self._initial_function
        globals()['get_logger'] = self._initial_function
        manager = logging.Logger.manager
        for logger_name in self._loggers:
            manager.loggerDict.pop(logger_name, None)
        logging.lastResort = self._last_resort
        self._loggers = set()

