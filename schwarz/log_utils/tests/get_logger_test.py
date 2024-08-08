# -*- coding: utf-8 -*-
# Copyright (c) 2013-2016, 2019, 2022, 2024 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

import pytest
from testfixtures import LogCapture

from ..log_proxy import get_logger
from ..testutils import LogHelper


@pytest.fixture
def log_helper():
    _log_helper = LogHelper.set_up(globals_=globals())
    try:
        yield
    finally:
        _log_helper.cleanup()

def test_get_logger_can_return_regular_python_loggers(log_helper):
    with LogCapture() as l_:
        log = get_logger('bar')
        log.info('hello world')
    l_.check(('bar', 'INFO', 'hello world'),)

def test_get_logger_can_log_to_passed_logger(log_helper):
    with LogCapture() as l_:
        bar_logger = logging.getLogger('bar')
        log = get_logger('foo', log=bar_logger)
        log.info('logged via bar not foo')
    l_.check(('bar', 'INFO', 'logged via bar not foo'),)

def test_get_logger_can_disable_logging(log_helper):
    with LogCapture() as l_:
        log = get_logger('foo', log=False)
        log.debug('foo %s', 'bar')
        log.warning('foo %s', 'bar')
        log.error('foo %s', 'bar')
        # need to cause an exception so log.exception works...
        try:
            log.invalid
        except:
            log.exception('foo %s', 'bar')

        assert len(l_.records) == 0, \
            'must not log messages via Python loggers when using "log=False"'

        # ensure that the fake logger from the beginning of this test does
        # not make any permanent changes and we can still use regular
        # loggers.
        pylog = logging.getLogger('foo')
        pylog.info('should log this')
        l_.check(('foo', 'INFO', 'should log this'),)

def test_get_logger_can_pass_log_level(log_helper):
    with LogCapture() as l_:
        log = get_logger('bar', level=logging.WARN)
        log.info('hello world')
        log.warning('something went wrong!')
    l_.check(('bar', 'WARNING', 'something went wrong!'),)

