# -*- coding: utf-8 -*-
# Copyright (c) 2020, 2022 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from pythonic_testcase import *
from testfixtures import LogCapture

from .. import get_logger, l_, CallbackLogger


class CallbackLoggerTest(PythonicTestCase):
    def test_can_call_function_when_handling_message_above_threshold(self):
        callback_msgs = []
        mock_fn = callback_msgs.append

        with LogCapture() as l_:
            log = get_logger('bar')
            l = CallbackLogger(callback=mock_fn, callback_minlevel=logging.WARN, log=log)
            l.info('regular message')
            assert_length(0, callback_msgs)
    
            l.warning('some warning')
            assert_equals(['some warning'], callback_msgs)
    
            l.error('serious problem')
            assert_length(2, callback_msgs)
            assert_equals('serious problem', callback_msgs[-1])

        l_.check(
            ('bar', 'INFO',    'regular message'),
            ('bar', 'WARNING', 'some warning'),
            ('bar', 'ERROR',   'serious problem'),
        )

    def test_can_merge_arguments_into_placeholders(self):
        callback_msgs = []
        l = CallbackLogger(
            log      = l_(None),
            callback = callback_msgs.append,
            callback_minlevel = logging.INFO,
        )
        l.info('name: %s', 'foo')
        assert_equals(['name: foo'], callback_msgs)

    def test_can_pass_raw_records_to_callback(self):
        callback_records = []
        l = CallbackLogger(
            log      = l_(None),
            callback = callback_records.append,
            merge_arguments   = False,
            callback_minlevel = logging.INFO,
        )
        l.info('name: %s', 'foo')

        record, = callback_records
        assert_equals('name: %s', record.msg)
        assert_equals(('foo',), record.args)
        assert_equals('INFO', record.levelname)

