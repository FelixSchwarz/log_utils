# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, 2019, 2022 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging
import sys

from pythonic_testcase import *
from testfixtures import LogCapture

from ..log_proxy import get_logger
from ..testutils import LogHelper


class GetLoggerTest(PythonicTestCase):
    def setUp(self):
        self.log_helper = LogHelper.set_up(test=self, globals_=globals())

    def test_can_return_regular_python_loggers(self):
        with LogCapture() as l_:
            log = get_logger('bar')
            log.info('hello world')
        l_.check(('bar', 'INFO', 'hello world'),)

    def test_can_log_to_passed_logger(self):
        with LogCapture() as l_:
            bar_logger = logging.getLogger('bar')
            log = get_logger('foo', log=bar_logger)
            log.info('logged via bar not foo')
        l_.check(('bar', 'INFO', 'logged via bar not foo'),)

    def test_can_disable_logging(self):
        with LogCapture() as l_:
            log = get_logger('foo', log=False)
            log.debug('foo %s', 'bar')
            if sys.version_info < (3, 0):
                # using "log.warn()" triggers a DeprecationWarning in Python 3
                log.warn('foo %s', 'bar')
            log.warning('foo %s', 'bar')
            log.error('foo %s', 'bar')
            # need to cause an exception so log.exception works...
            try:
                log.invalid
            except:
                log.exception('foo %s', 'bar')

            assert_length(0, l_.records,
                message='must not log messages via Python loggers when using "log=False"')

            # ensure that the fake logger from the beginning of this test does
            # not make any permanent changes and we can still use regular
            # loggers.
            pylog = logging.getLogger('foo')
            pylog.info('should log this')
            l_.check(('foo', 'INFO', 'should log this'),)

    def test_can_pass_log_level(self):
        with LogCapture() as l_:
            log = get_logger('bar', level=logging.WARN)
            log.info('hello world')
            log.warning('something went wrong!')
        l_.check(('bar', 'WARNING', 'something went wrong!'),)

