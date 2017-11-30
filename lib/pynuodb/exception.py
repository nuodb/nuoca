# Copyright (c) 2017, NuoDB, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of NuoDB, Inc. nor the names of its contributors may
#       be used to endorse or promote products derived from this software
#       without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL NUODB, INC. BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Classes containing the exceptions for reporting errors."""

from . import protocol

__all__ = ['Warning', 'Error', 'InterfaceError', 'DatabaseError', 'BatchError', 'DataError',
           'OperationalError', 'IntegrityError', 'InternalError',
           'ProgrammingError', 'NotSupportedError', 'EndOfStream', 'db_error_handler']


class Warning(Exception):
    def __init__(self, value):
        self.__value = value

    def __str__(self):
        return repr(self.__value)


class Error(Exception):
    def __init__(self, value):
        self.__value = value

    def __str__(self):
        return repr(self.__value)


class InterfaceError(Error):
    def __init__(self, value):
        Error.__init__(self, value)


class DatabaseError(Error):
    def __init__(self, value):
        Error.__init__(self, value)


class BatchError(DatabaseError):
    results = None

    def __init__(self, value, results):
        Error.__init__(self, value)
        self.results = results


class DataError(DatabaseError):
    def __init__(self, value):
        DatabaseError.__init__(self, value)


class OperationalError(DatabaseError):
    def __init__(self, value):
        DatabaseError.__init__(self, value)


class IntegrityError(DatabaseError):
    def __init__(self, value):
        DatabaseError.__init__(self, value)


class InternalError(DatabaseError):
    def __init__(self, value):
        DatabaseError.__init__(self, value)


class ProgrammingError(DatabaseError):
    def __init__(self, value):
        DatabaseError.__init__(self, value)


class NotSupportedError(DatabaseError):
    def __init__(self, value):
        DatabaseError.__init__(self, value)


class EndOfStream(Exception):
    def __init__(self, value):
        self.__value = value

    def __str__(self):
        return repr(self.__value)


def db_error_handler(error_code, error_string):
    """
    :type error_code int
    :type error_string str
    """
    error_code_string = protocol.lookup_code(error_code)
    if error_code in protocol.DATA_ERRORS:
        raise DataError(error_code_string + ': ' + error_string)
    elif error_code in protocol.OPERATIONAL_ERRORS:
        raise OperationalError(error_code_string + ': ' + error_string)
    elif error_code in protocol.INTEGRITY_ERRORS:
        raise IntegrityError(error_code_string + ': ' + error_string)
    elif error_code in protocol.INTERNAL_ERRORS:
        raise InternalError(error_code_string + ': ' + error_string)
    elif error_code in protocol.PROGRAMMING_ERRORS:
        raise ProgrammingError(error_code_string + ': ' + error_string)
    elif error_code in protocol.NOT_SUPPORTED_ERRORS:
        raise NotSupportedError(error_code_string + ': ' + error_string)
    else:
        raise DatabaseError(error_code_string + ': ' + error_string)
