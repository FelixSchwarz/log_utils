# -*- coding: utf-8 -*-
# Copyright (c) 2019 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

import logging

from pythonic_testcase import *
from testfixtures import LogCapture

from ..log_proxy import get_logger, ForwardingLogger
from ..testutils import LogHelper


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

