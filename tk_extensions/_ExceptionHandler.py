
import sys
import tkinter as tk
from tkinter import messagebox

#===================================================================================================
_HANDLER = None

def _top_error_handler(*exc_info):
    if(_HANDLER != None):
        _HANDLER.handler(*exc_info)
    
def _top_tk_error_handler(self, *args):
    _top_error_handler(*args)

#===================================================================================================
    
class ExceptionHandler(object):
    
    @staticmethod
    def handler(*exc_info):
        exc_type = exc_info[0]
        exc_value = exc_info[1]
        
        messagebox.showerror(
            title = "Internal Error",
            message = "Oops! Something went wrong!\n\n"
                     +"Type: %s\n\n" % exc_type.__name__
                     +"Value: %s" % exc_value
        )
        
    @classmethod
    def install(cls):
        global _HANDLER
        _HANDLER = cls
        sys.excepthook = _top_error_handler
        tk.Tk.report_callback_exception = _top_tk_error_handler
    