class UserProfileNotProvidedError(Exception): 
    pass

class InvalidFinanceParameterError(Exception):
    def __init__(self, errored_parameter:str, erring_parameter:str):
        message = f"Cannot compute '{errored_parameter}' due to invalid (possibly zero) value of '{erring_parameter}'."
        super().__init__(message)

class InvalidJsonFormatError(Exception):
    def __init__(self, var:str):
        message = f"Expected {var} to be JSON style-string."
        super().__init__(message)

class NoMarkdownFileToConvertToPDFError(Exception):...