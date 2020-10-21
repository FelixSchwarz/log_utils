# -*- coding: utf-8 -*-
# Copyright (c) 2020 Felix Schwarz
# The source code contained in this file is licensed under the MIT license.
# SPDX-License-Identifier: MIT

import logging

from .log_proxy import l_


__all__ = ['CallbackLogger']

class CallbackLogger(logging.Logger):
    """
    A `Logger`-like class which can trigger a additional callback in addition
    to passing a log message through the logging infrastructure. I'm using this
    to ensure severe problems logged by lower-level libraries will be displayed
    in the UI.

    If you set `merge_arguments = True` the callback only gets the final
    message (as `str`), otherwise it'll get the `logging.LogRecord`.
    """
    def __init__(self, *args, **kwargs):
        self._callback = kwargs.pop('callback')
        self._callback_minlevel = kwargs.pop('callback_minlevel', logging.NOTSET)
        self.__logger = l_(kwargs.pop('log'))

        merge_arguments = kwargs.pop('merge_arguments', True)
        self.formatter = logging.Formatter(fmt='%(message)s') if merge_arguments else None

        if (not args) and ('name' not in kwargs):
            name = self.__class__.__name__
            args = (name, )
        super(CallbackLogger, self).__init__(*args, **kwargs)

    def callHandlers(self, record):
        # "logging.NOTSET" (default) is defined as 0 so that works here just fine
        if (record.levelno >= self._callback_minlevel) and (self._callback is not None):
            callback_args = (self.formatter.format(record),) if self.formatter else (record,)
            self._callback(*callback_args)
        self.__logger.log(record.levelno, record.msg, *record.args)

