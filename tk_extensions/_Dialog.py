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
class Dialog(object):
    """
    Generic dialog parent class
    """

    def __init__(self, parent = None, title = None):
        
        if(parent):
            # Has a defined parent.
            self.tkWindow = tk.Toplevel(parent)
            self.tkWindow.transient(parent)
            self.tkWindow.parent = parent
            self.tkWindow.foster_parent = None
        else:
            # Headless Dialog. Create foster parent
            foster_parent = tk.Tk()
            foster_parent.withdraw()
            self.tkWindow = tk.Toplevel(foster_parent)
            self.tkWindow.parent = None
            self.tkWindow.foster_parent = foster_parent
            
        #--------------------------------------------------------
        # Create Widgets
        
        if title:
            self.tkWindow.title(title)
        
        fr_body = ttk.Frame(
            self.tkWindow,
            padding = 5
        )
        self.create_body(fr_body)
        fr_body.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        ttk.Separator(
            self.tkWindow
        ).pack(side=tk.TOP, fill=tk.X)
        
        fr_buttonbox = ttk.Frame(
            self.tkWindow,
            padding = 5
        )
        self.create_buttonbox(fr_buttonbox)
        fr_buttonbox.pack(side=tk.BOTTOM, fill=tk.X)
        
        #--------------------------------------------------------
        
        # window is not allowed to be any smaller than default
        self.tkWindow.update_idletasks() #Give Tk a chance to update widgets and figure out the window size
        self.tkWindow.minsize(self.tkWindow.winfo_width(), self.tkWindow.winfo_height())
        
        if(self.tkWindow.parent):
            # Place dialog on top of parent window
            self.tkWindow.grab_set()
            self.tkWindow.geometry("+%d+%d" % (self.tkWindow.parent.winfo_rootx()+50,
                                               self.tkWindow.parent.winfo_rooty()+50))
        
        # User initialize routines
        self.dlg_initialize()
        
        # block until the window exits
        self.tkWindow.wait_window(self.tkWindow)
    
    #---------------------------------------------------------------
    # Construction Hooks
    #---------------------------------------------------------------
    def create_body(self, master_fr):
        """
        Create dialog body.
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
        self.tkWindow.protocol("WM_DELETE_WINDOW", self.dlg_pbCancel)
        
    #---------------------------------------------------------------
    # Standard button actions
    #---------------------------------------------------------------
    def dlg_pbOK(self, event=None):
        
        if(self.dlg_validate() == False):
            return
        self.dlg_apply()
        self.result = True
        
        self.tkWindow.withdraw()
        self.tkWindow.update_idletasks()
        
        if(self.tkWindow.parent):
            # put focus back to the parent window
            self.tkWindow.parent.focus_set()
        
        self.tkWindow.destroy()
        
        if(self.tkWindow.foster_parent):
            self.tkWindow.foster_parent.destroy()
        
    def dlg_pbCancel(self, event=None):
        self.result = False
        
        self.tkWindow.withdraw()
        self.tkWindow.update_idletasks()
        
        if(self.tkWindow.parent):
            # put focus back to the parent window
            self.tkWindow.parent.focus_set()
        
        self.tkWindow.destroy()
        
        if(self.tkWindow.foster_parent):
            self.tkWindow.foster_parent.destroy()
    
    #---------------------------------------------------------------
    # Standard Action hooks
    #---------------------------------------------------------------
    def dlg_initialize(self):
        """
        This is called once all objects in the dialog have been created.
        Override this to initialize dialog widgets.
        """
        pass # override
        
    def dlg_validate(self):
        """
        This is called prior to exiting the dialog to validate the dialog contents prior to applying
        them.
        If False is returned, the dialog does not exit.
        If True is returned, dlg_apply() is called, and the dialog exits.
        """
        return(True) # override
    
    def dlg_apply(self):
        """
        This is called prior to exit when accepting the contents of the dialog.
        Contents have already been validated, and can be stored in local variables
        """
        pass # override


####################################################################################################
# Example
####################################################################################################
if __name__ == '__main__':
    from tkinter import messagebox
    
    class ExampleDialog(Dialog):
        def __init__(self, my_text):
            # Set up user-variables here
            self.my_text = my_text
            
            # Start the dialog. This blocks until done.
            Dialog.__init__(self, parent = None, title = "Example")
        
        def create_body(self, master_fr):
            # Construct the contents of the dialog
            self.txt_textbox = ttk.Entry(
                master_fr
            )
            self.txt_textbox.pack()
            
        def dlg_initialize(self):
            # Initialize dialog objects from any user-variables set during __init__()
            self.txt_textbox.delete(0, tk.END)
            self.txt_textbox.insert(tk.END, self.my_text)
            
        def dlg_validate(self):
            # Check if user input is valid
            if(len(self.txt_textbox.get()) == 0):
                messagebox.showerror(
                    title = "Error!",
                    message = "Text box cannot be empty."
                )
                return(False)
            
            return(True)
            
        def dlg_apply(self):
            # Save contents of dialog into variables
            self.my_text = self.txt_textbox.get()
    
    
    dlg = ExampleDialog("test text")
    if(dlg.result):
        print("User pressed OK. Textbox contents: %s " % dlg.my_text)
    else:
        print("User pressed cancel or closed window.")
    