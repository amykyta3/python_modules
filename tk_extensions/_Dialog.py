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
class Dialog(tk.Toplevel):
    """
    Generic dialog parent class
    """

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
        
        # User initialize routines
        self.dlg_initialize()
        
        # block until the window exits
        self.wait_window(self)
    
    #---------------------------------------------------------------
    # Construction Hooks
    #---------------------------------------------------------------
    def create_body(self, master_fr):
        """
        Create dialog body.
        Return widget that should have initial focus.
        This method should be overridden.
        """
        pass
    
    def create_buttonbox(self, master_fr):
        """
        Add standard button box.
        Override if you don't want the default buttons
        """
        
        ttk.Button(
            master_fr,
            text="Cancel",
            command=self.dlg_pbCancel
        ).pack(side=tk.RIGHT)
        
        ttk.Button(
            master_fr,
            text="OK",
            command=self.dlg_pbOK,
            default=tk.ACTIVE
        ).pack(side=tk.RIGHT)
        
        # Do Cancel if closed
        self.protocol("WM_DELETE_WINDOW", self.dlg_pbCancel)
        
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
        return(True) # override
    
    def dlg_apply(self):
        pass # override


####################################################################################################
# Example
####################################################################################################
if __name__ == '__main__':
    from tkinter import messagebox
    
    class ExampleDialog(Dialog):
        def __init__(self, my_text):
            self.my_text = my_text
            
            Dialog.__init__(self, parent = None, title = "Example")
        
        def create_body(self, master_fr):
            self.txt_textbox = ttk.Entry(
                master_fr
            )
            self.txt_textbox.pack()
            
        def dlg_initialize(self):
            
            self.txt_textbox.delete(0, tk.END)
            self.txt_textbox.insert(tk.END, self.my_text)
            
        def dlg_validate(self):
            if(len(self.txt_textbox.get()) == 0):
                messagebox.showerror(
                    title = "Error!",
                    message = "Text box cannot be empty."
                )
                return(False)
            
            return(True)
            
        def dlg_apply(self):
            self.my_text = self.txt_textbox.get()
    
    
    
    
    dlg = ExampleDialog("test text")
    
    if(dlg.result):
        print(dlg.my_text)
        
    else:
        print("Cancelled")
        
    import pprint
    pprint.pprint(vars(dlg))
    