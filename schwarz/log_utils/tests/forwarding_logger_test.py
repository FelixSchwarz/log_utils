# -*- coding: utf-8 -*-
# Copyright (c) 2019, 2022, 2024 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

from __future__ import absolute_import, print_function, unicode_literals

import logging
from logging import Formatter as LogFormatter

import pytest
from testfixtures import LogCapture

from .. import get_logger, ForwardingLogger
from ..testutils import LogHelper


@pytest.fixture
def log_helper():
    _log_helper = LogHelper.set_up()
    try:
        yield
    finally:
        _log_helper.cleanup()


def test_forwardinglogger_can_forward_with_prefix(log_helper):
    with LogCapture() as l_:
        log = get_logger('bar')
        wrapped_log = ForwardingLogger(forward_to=log, forward_prefix='[ABC] ', forward_minlevel=logging.INFO)
        wrapped_log.info('hello world')
        wrapped_log.debug('should be ignored')
    l_.check(('bar', 'INFO', '[ABC] hello world'),)

def test_forwardinglogger_can_forward_with_suffix(log_helper):
    with LogCapture() as l_:
        log = get_logger('bar')
        wrapped_log = ForwardingLogger(forward_to=log, forward_suffix=' (foo)')
        wrapped_log.info('hello world')
    l_.check(('bar', 'INFO', 'hello world (foo)'),)

def test_forwardinglogger_can_forward_exception_info(log_helper):
    exc_msg = 'something went wrong'
    with LogCapture() as l_:
        log = get_logger('bar')
        wrapped_log = ForwardingLogger(forward_to=log, forward_prefix='[FOO] ')
        try:
            raise ValueError(exc_msg)
        except ValueError:
            wrapped_log.exception('caught error')

    l_.check(('bar', 'ERROR', '[FOO] caught error'),)
    lr, = l_.records
    logged_text = LogFormatter('%(message)s').format(lr)
    assert logged_text.startswith('[FOO] caught error')
    assert 'Traceback (most recent call last)' in logged_text
    assert ('ValueError: ' + exc_msg) in logged_text

