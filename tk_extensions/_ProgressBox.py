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

import threading

####################################################################################################
class ProgressBox(tk.Toplevel):
    """
    Progress bar dialog box
    """
    def __init__(self, job_func, job_data = {}, parent = None, title = None):
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
        
        #--------------------------------------------------------
        # Create Widgets
        
        if title:
            self.title(title)
        else:
            self.title("Working...")
        
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
        
        self.resizable(False, False)
        
        if(self.parent):
            # Place dialog on top of parent window
            self.grab_set()
            self.geometry("+%d+%d" % (self.parent.winfo_rootx()+50,
                                      self.parent.winfo_rooty()+50))
        
        # Do Cancel if closed
        self.protocol("WM_DELETE_WINDOW", self.dlg_pbCancel)
        
        self.dlg_if = self.dialog_interface()
        
        worker = self.worker_thread(self.dlg_if, job_func, job_data)
        worker.start()
        
        # Loop here until the thread finishes
        while(worker.is_alive()):
            
            # Process any updates from the worker
            x = self.dlg_if.get_progress()
            if(x != None):
                self.bar.configure(value=x)
            
            x = self.dlg_if.get_status1()
            if(x != None):
                self.lbl_status1.configure(text=x)
            
            x = self.dlg_if.get_status2()
            if(x != None):
                self.lbl_status2.configure(text=x)
            
            # update Tk events
            self.update()
            
            
        # operation has completed. Close the window
        self.withdraw()
        self.update_idletasks()
        
        if(self.parent):
            self.parent.focus_set()
        
        self.destroy()
        
        if(self.foster_parent):
            self.foster_parent.destroy()
        
        if(worker.exc_info):
            # By the way, worker caught an exception. Raise it here
            raise worker.exc_info
            
        # Copy job_retval
        self.job_retval = worker.job_retval
        
    #---------------------------------------------------------------
    # Construction Hooks
    #---------------------------------------------------------------
    def create_body(self, master_fr):
        
        self.lbl_status1 = ttk.Label(
            master_fr,
        )
        self.lbl_status1.pack(
            side=tk.TOP,
            fill=tk.X
        )
        
        self.lbl_status2 = ttk.Label(
            master_fr,
        )
        self.lbl_status2.pack(
            side=tk.TOP,
            fill=tk.X
        )
        
        self.bar = ttk.Progressbar(
            master_fr,
            length=300
        )
        self.bar.pack(
            side=tk.TOP,
            pady=5
        )
    
    def create_buttonbox(self, master_fr):
        
        ttk.Button(
            master_fr,
            text="Cancel",
            command=self.dlg_pbCancel
        ).pack(side=tk.RIGHT)
        
    #---------------------------------------------------------------
    # Events
    #---------------------------------------------------------------
    def dlg_pbCancel(self, event=None):
        # only allow one click
        if(not self.dlg_if.stop_requested()):
            self.dlg_if.request_stop()
            
            self.bar.configure(value=0)
            self.lbl_status1.configure(text="Cancelling...")
            self.lbl_status2.configure(text="Please Wait")
        
    #---------------------------------------------------------------
    
    class worker_thread(threading.Thread):
        def __init__(self, dlg_if, job_func, job_data = {}):
            threading.Thread.__init__(self)
            
            self.dlg_if = dlg_if
            self.job_func = job_func
            self.job_data = job_data
            
            self.exc_info = None
            self.job_retval = None
        
        def run(self):
            try:
                self.run_body()
            except Exception as E:
                self.exc_info = E
            
        def run_body(self):
            self.job_retval = self.job_func(self.dlg_if, **self.job_data)

    class dialog_interface:
        def __init__(self):
            self.stop_request_var = False
            
            self.lock = threading.Lock()
            self.status1 = ""
            self.status2 = ""
            self.percent = 0
        
        #----------------------------------------
        # Dialog's interface
        #----------------------------------------
        def request_stop(self):
            self.stop_request_var = True
        
        def get_progress(self):
            if(self.stop_request_var):
                return(None)
            self.lock.acquire()
            percent = self.percent
            self.percent = None
            self.lock.release()
            return(percent)
            
        def get_status1(self):
            if(self.stop_request_var):
                return(None)
            self.lock.acquire()
            status1 = self.status1
            self.status1 = None
            self.lock.release()
            return(status1)
        
        def get_status2(self):
            if(self.stop_request_var):
                return(None)
            self.lock.acquire()
            status2 = self.status2
            self.status2 = None
            self.lock.release()
            return(status2)
            
        #----------------------------------------
        # Worker thread's interface
        #----------------------------------------
        def stop_requested(self):
            return(self.stop_request_var)
            
        def set_progress(self, percent):
            self.lock.acquire()
            self.percent = percent
            self.lock.release()
            
        def set_status1(self, text):
            self.lock.acquire()
            self.status1 = text
            self.lock.release()
        
        def set_status2(self, text):
            self.lock.acquire()
            self.status2 = text
            self.lock.release()

####################################################################################################
# Example
####################################################################################################
if __name__ == '__main__':
    import time
    
    # This is a list of data that I have to do some processing on
    my_list_of_data = [
        "foo",
        "bar",
        "foobar",
        "barfoo"
    ]
    
    # Create a function that will do the work.
    # dlg_if is required. Other args are for whatever is needed to pass in.
    def my_job_function(dlg_if, my_foobar_list):
        n_items = len(my_foobar_list)
        n_items_done = 0
        processed_foobar = []
        
        for foobar in my_foobar_list:
            dlg_if.set_status1("Processing FooBars: %d of %d" % (n_items_done+1, n_items))
            dlg_if.set_status2("%s" % foobar)
            dlg_if.set_progress(100*n_items_done/n_items)
            
            if(dlg_if.stop_requested()):
                return(None)
            
            # Do some really hard work
            processed_foobar.append(foobar.upper())
            time.sleep(1)
            
            n_items_done += 1
        
        return(processed_foobar)
    
    # Package args that will be passed to the job function
    my_job_args = {
        'my_foobar_list': my_list_of_data
    }
    
    # Run the job through the ProgressBox
    job = ProgressBox(
        job_func = my_job_function,
        job_data = my_job_args,
        parent = None,
        title = "Doing some work..."
    )
    
    if(job.job_retval == None):
        print("Exited early")
    else:
        print(job.job_retval)