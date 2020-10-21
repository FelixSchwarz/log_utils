# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from pythonic_testcase import *
from testfixtures import LogCapture

from .. import get_logger


class GetLoggerTest(PythonicTestCase):
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

