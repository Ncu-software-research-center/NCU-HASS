class Response(object):
    def __init__(self, code, message=None, data=None):
        self.code = code
        self.message = message
        self.data = data
