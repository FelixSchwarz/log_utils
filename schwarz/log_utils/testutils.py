# -*- coding: utf-8 -*-
# Copyright (c) 2020-2021 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from .log_proxy import CollectingHandler


__all__ = [
    'assert_did_log_message',
    'assert_no_log_messages',
    'build_collecting_logger',
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
            return

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

