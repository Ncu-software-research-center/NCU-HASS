#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

class Response(object):
    def __init__(self, code, message=None, data=None):
        self.code = code
        self.message = message
        self.data = data
