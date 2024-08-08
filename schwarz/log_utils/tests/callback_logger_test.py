# -*- coding: utf-8 -*-
# Copyright (c) 2020, 2022, 2024 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from testfixtures import LogCapture

from .. import get_logger, l_, CallbackLogger


def test_callback_logger_can_call_function_when_handling_message_above_threshold():
    callback_msgs = []
    mock_fn = callback_msgs.append

    with LogCapture() as l_:
        log = get_logger('bar')
        l = CallbackLogger(callback=mock_fn, callback_minlevel=logging.WARN, log=log)
        l.info('regular message')
        assert len(callback_msgs) == 0

        l.warning('some warning')
        assert callback_msgs == ['some warning']

        l.error('serious problem')
        assert len(callback_msgs) == 2
        assert callback_msgs[-1] == 'serious problem'

    l_.check(
        ('bar', 'INFO',    'regular message'),
        ('bar', 'WARNING', 'some warning'),
        ('bar', 'ERROR',   'serious problem'),
    )

def test_callback_logger_can_merge_arguments_into_placeholders():
    callback_msgs = []
    l = CallbackLogger(
        log      = l_(None),
        callback = callback_msgs.append,
        callback_minlevel = logging.INFO,
    )
    l.info('name: %s', 'foo')
    assert callback_msgs == ['name: foo']

def test_callback_logger_can_pass_raw_records_to_callback():
    callback_records = []
    l = CallbackLogger(
        log      = l_(None),
        callback = callback_records.append,
        merge_arguments   = False,
        callback_minlevel = logging.INFO,
    )
    l.info('name: %s', 'foo')

    record, = callback_records
    assert record.msg == 'name: %s'
    assert record.args == ('foo',)
    assert record.levelname == 'INFO'

