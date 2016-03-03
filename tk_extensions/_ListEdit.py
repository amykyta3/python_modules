####################################################################################################
# The MIT License (MIT)
#
# Copyright (c) 2016, Alexander I. Mykyta
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
from ._Dialog import Dialog

####################################################################################################
class ListEdit(Dialog):
    """
    Generic base-class for a list editor
    """

    def __init__(self, parent = None, title = None, item_list = []):
        
        """
        item_list is a list of objects to be manipulated
        Remember: Python lists are passed by reference! This dialog assumes you have
        already made a backup copy before starting this dialog.
        Changes should only be committed if this dialog returns result=True
        """
        self.item_list = item_list
        
        Dialog.__init__(self, parent = parent, title = title)
    
    #---------------------------------------------------------------
    # Construction Hooks
    #---------------------------------------------------------------
    def create_body(self, master_fr):
        
        fr_entries = ttk.Frame(master_fr)
        fr_entries.pack(side = tk.RIGHT, fill = tk.BOTH, expand=True)
        
        #----------------
        # Entry list and scrollbar
        #----------------
        sb_list = ttk.Scrollbar(fr_entries)
        sb_list.pack(
            side = tk.RIGHT,
            fill = tk.Y
        )
        self.lb_items = tk.Listbox(
            fr_entries,
            highlightthickness = 0,
            activestyle = "none",
            exportselection = False,
            selectmode = "single"
        )
        self.lb_items.bind('<Double-1>', lambda x: self.on_pb_Edit())
        self.lb_items.pack(
            side = tk.RIGHT,
            fill = tk.BOTH,
            expand = True
        )
        self.lb_items.configure(yscrollcommand=sb_list.set)
        sb_list.configure(command=self.lb_items.yview)
        
        #----------------
        # Entry List side buttons
        #----------------
        fr_list_controls = ttk.Frame(master_fr, padding=5)
        fr_list_controls.pack(
            side = tk.LEFT,
            fill = tk.Y
        )
        
        ttk.Button(fr_list_controls,
            text="Add",
            command=self.on_pb_Add
        ).pack(side = tk.TOP)
        
        ttk.Button(fr_list_controls,
            text="Delete",
            command=self.on_pb_Delete
        ).pack(side = tk.TOP)
        
        ttk.Button(fr_list_controls,
            text="Edit",
            command=self.on_pb_Edit
        ).pack(side = tk.TOP)
        
        ttk.Button(fr_list_controls,
            text="Down",
            command=self.on_pb_Down
        ).pack(side = tk.BOTTOM)
        
        ttk.Button(fr_list_controls,
            text="Up",
            command=self.on_pb_Up
        ).pack(side = tk.BOTTOM)
    
    def dlg_initialize(self):
        for I in self.item_list:
            self.lb_items.insert(tk.END, self.get_item_label(I))
        
    def on_pb_Up(self):
        idx = self.lb_items.curselection()
        if(len(idx) == 0):
            return
        idx = int(idx[0])
        
        if(idx <= 0):
            return
        
        I = self.item_list.pop(idx)
        self.lb_items.delete(idx)
        
        self.item_list.insert(idx-1, I)
        self.lb_items.insert(idx-1, self.get_item_label(I))
        self.lb_items.selection_clear(0,tk.END)
        self.lb_items.selection_set(idx-1)
        self.lb_items.see(idx-1)
        
    def on_pb_Down(self):
        idx = self.lb_items.curselection()
        if(len(idx) == 0):
            return
        idx = int(idx[0])
        
        if(idx >= len(self.item_list)-1):
            return
        
        I = self.item_list.pop(idx)
        self.lb_items.delete(idx)
        
        self.item_list.insert(idx+1, I)
        self.lb_items.insert(idx+1, self.get_item_label(I))
        self.lb_items.selection_clear(0,tk.END)
        self.lb_items.selection_set(idx+1)
        self.lb_items.see(idx+1)
    
    def on_pb_Delete(self):
        idx = self.lb_items.curselection()
        if(len(idx)):
            idx = int(idx[0])
            if(self.deleting_item(self.item_list[idx]) == False):
                return
            
            del self.item_list[idx]
            self.lb_items.delete(idx)
            
            if(idx >= len(self.item_list)):
                idx = len(self.item_list) - 1
            
            self.lb_items.selection_clear(0,tk.END)
            self.lb_items.selection_set(idx)
            self.lb_items.see(idx)
            
    def on_pb_Add(self):
        I = self.new_item()
        if(I == None):
            return
        
        self.item_list.append(I)
        self.lb_items.insert(tk.END, self.get_item_label(I))
        self.lb_items.selection_clear(0,tk.END)
        self.lb_items.selection_set(len(self.item_list)-1)
        self.lb_items.see(len(self.item_list)-1)
        
    def on_pb_Edit(self):
        idx = self.lb_items.curselection()
        if(len(idx) == 0):
            return
        idx = int(idx[0])
        
        I = self.edit_item(self.item_list[idx])
        if(I == None):
            return
        self.item_list[idx] = I
        
        # update label
        self.lb_items.delete(idx)
        self.lb_items.insert(idx, self.get_item_label(I))
        self.lb_items.selection_set(idx)
        
    #---------------------------------------------------------------
    # User Functions
    #---------------------------------------------------------------
    def get_item_label(self, I):
        """
        Given an item, return an identifier string to use in the list
        """
        return("name")
    
    def deleting_item(self, I):
        """
        Item I is about to be removed from the list.
        Do cleanup actions if necessary
        If item cannot be removed, return False to cancel
        """
        return(True)
        
    def new_item(self):
        """
        Create a new item.
        Return it once created.
        Return None if item won't be created
        """
        return(None)
        
    def edit_item(self, I):
        """
        Editing the item
        Return the edited item
        Return None if the item was not changed after all
        """
        return(None)

####################################################################################################
# Example
####################################################################################################
if __name__ == '__main__':
    from tkinter import messagebox
    
    class ExampleListEdit(ListEdit):
        def __init__(self, my_list):
            
            # Start the dialog. This blocks until done.
            ListEdit.__init__(self, parent = None, title = "Example", item_list = my_list)
        
        def get_item_label(self, I):
            return(I)
        
        def new_item(self):
            return("NEW!")
            
        def edit_item(self, I):
            if(len(I) < 8):
                I += "x"
            return(I)
    
    my_list = [
        "hello",
        "world",
        "this",
        "is",
        "my",
        "list"
    ]
    
    my_backup_list = my_list.copy()
    dlg = ExampleListEdit(my_list)
    if(dlg.result):
        print("User pressed OK")
    else:
        print("User pressed cancel or closed window.")
        my_list = my_backup_list
        
    print(my_list)
    