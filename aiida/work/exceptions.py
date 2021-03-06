# -*- coding: utf-8 -*-
###########################################################################
# Copyright (c), The AiiDA team. All rights reserved.                     #
# This file is part of the AiiDA code.                                    #
#                                                                         #
# The code is hosted on GitHub at https://github.com/aiidateam/aiida_core #
# For further information on the license, see the LICENSE.txt file        #
# For further information please visit http://www.aiida.net               #
###########################################################################
"""Exceptions that can be thrown by parts of the workflow engine."""
from __future__ import absolute_import
from aiida.common.exceptions import AiidaException

__all__ = ['PastException']


class PastException(AiidaException):
    """
    Raised when an attempt is made to continue a Process that has already excepted before
    """
    pass
