# -*- coding: utf-8 -*-
# Copyright (c) 2021 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from pythonic_testcase import assert_raises, PythonicTestCase

from ..testutils import (assert_did_log_message, assert_no_log_messages,
    build_collecting_logger)


class TestutilsTest(PythonicTestCase):
    def test_can_assert_logged_messages(self):
        log, lc = build_collecting_logger()
        log.info('foo')
        log.debug('bar')

        assert_did_log_message(lc, 'foo')
        assert_did_log_message(lc, 'foo', level=logging.INFO)
        with assert_raises(AssertionError):
            assert_did_log_message(lc, 'foo', level=logging.DEBUG)
        assert_no_log_messages(lc, min_level=logging.WARN)

