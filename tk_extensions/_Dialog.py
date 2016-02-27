####################################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2015, Alexander I. Mykyta
# All rights reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
####################################################################################################

import tkinter as tk
from tkinter import ttk

####################################################################################################
# Generic dialog parent class
class Dialog(tk.Toplevel):

    def __init__(self, parent = None, title = None):
        if(parent):
            # Has a defined parent.
            self.parent = parent
            self.foster_parent = None
            tk.Toplevel.__init__(self, self.parent)
            self.transient(self.parent)
        else:
            # Headless Dialog. Create foster parent
            self.foster_parent = tk.Tk()
            self.parent = None
            self.foster_parent.withdraw()
            tk.Toplevel.__init__(self, self.foster_parent)
            
        self.result = None
        
        #--------------------------------------------------------
        # Create Widgets
        
        if title:
            self.title(title)
        
        body = ttk.Frame(
            self,
            padding = 5
        )
        self.create_body(body)
        body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        buttonbox = ttk.Frame(
            self,
            padding = 5
        )
        self.create_buttonbox(buttonbox)
        buttonbox.pack(side=tk.BOTTOM, fill=tk.X)
        
        #--------------------------------------------------------
        
        # window is not allowed to be any smaller than default
        self.update_idletasks() #Give Tk a chance to update widgets and figure out the window size
        self.minsize(self.winfo_width(), self.winfo_height())
        
        if(self.parent):
            # Place dialog on top of parent window
            self.grab_set()
            self.geometry("+%d+%d" % (self.parent.winfo_rootx()+50,
                                      self.parent.winfo_rooty()+50))
        
        # Do Cancel if closed
        self.protocol("WM_DELETE_WINDOW", self.dlg_pbCancel)
        
        # User initialize routines
        self.dlg_initialize()
        
        # block until the window exits
        self.wait_window(self)
    
    #---------------------------------------------------------------
    # Construction Hooks
    #---------------------------------------------------------------
    def create_body(self, master_fr):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass
    
    def create_buttonbox(self, master_fr):
        # add standard button box. override if you don't want the
        # standard buttons
        
        w = ttk.Button(
            master_fr,
            text="Cancel",
            command=self.dlg_pbCancel
        )
        w.pack(side=tk.RIGHT)
        
        w = ttk.Button(
            master_fr,
            text="OK",
            command=self.dlg_pbOK,
            default=tk.ACTIVE
        )
        w.pack(side=tk.RIGHT)
        
        
    #---------------------------------------------------------------
    # Standard button actions
    #---------------------------------------------------------------
    def dlg_pbOK(self, event=None):
        
        if(self.dlg_validate() == False):
            return
        self.dlg_apply()
        self.result = True
        
        self.withdraw()
        self.update_idletasks()
        
        if(self.parent):
            # put focus back to the parent window
            self.parent.focus_set()
        
        self.destroy()
        
        if(self.foster_parent):
            self.foster_parent.destroy()
        
    def dlg_pbCancel(self, event=None):
        self.result = False
        
        self.withdraw()
        self.update_idletasks()
        
        if(self.parent):
            # put focus back to the parent window
            self.parent.focus_set()
        
        self.destroy()
        
        if(self.foster_parent):
            self.foster_parent.destroy()
    
    #---------------------------------------------------------------
    # Standard Action hooks
    #---------------------------------------------------------------
    def dlg_initialize(self):
        pass # override
        
    def dlg_validate(self):
        return True # override
    
    def dlg_apply(self):
        pass # override
