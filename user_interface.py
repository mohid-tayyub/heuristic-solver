#  Copyright (c) 2020 Mohid Tayyub. All rights reserved.
 
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
 
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
# AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import tkinter as tk
from tkinter import filedialog
from tkinter import IntVar
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
from Solvers.simulated_annealing import saPartitionSolver
from instances import netlist
from instances import module
from instances import net
from instances import utility
import time
import os 

class main_ui:
    def __init__(self,isrootwindow = True,root = None):
        self.new_module = None
        self.module_1_selected = None
        self.module_2_selected = None
        self.drag_active = False
        self.new_module_active = False
        self.redraw_time = 1
        self.x = 0
        self.y = 0

        #create tkinter widgets
        if(isrootwindow):
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(root)
            
        self.root.title("Main")
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.kill = False

        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Generate Netlist", command=self.genNetlist)
        self.filemenu.add_command(label="Import Netlist", command=self.importNetlist)
        self.menubar.add_cascade(label="File", menu=self.filemenu)

        self.solvemenu = tk.Menu(self.menubar, tearoff=0)
        self.solvemenu.add_command(label="Simulated Annealing", command=self.runSimulatedAnnealingUI)
        self.menubar.add_cascade(label="Solve", menu=self.solvemenu)

        self.root.config(menu=self.menubar)

        self.left_frame = tk.Frame(self.root)
        self.right_frame = tk.Frame(self.root)
        self.top_right_frame = tk.Frame(self.root)
        self.bottom_right_frame = tk.Frame(self.root)
    

        self.left_frame.pack(side = "left")
        self.right_frame.pack(side='right',fill = "both",expand=True)
        self.top_right_frame.pack(in_=self.right_frame,side="top",fill = "both",expand=True)
        self.bottom_right_frame.pack(in_=self.right_frame,side="bottom",fill="x")


        self.canv = tk.Canvas(self.root, bg="gray10", height=500, width=900)
        self.create_module_btn = tk.Button(self.root,text ="Create Module",command=self.createModule)
        self.clear_log_btn = tk.Button(self.root,text="Clear",command=self.clearLog)

        text_module_entry=tk.StringVar()
        text_module_entry.set("Enter Name of Module:")
        self.label_module_entry = tk.Label(self.root, textvariable=text_module_entry, height=1)
        vcmd = (self.root.register(self.validate_name), "%d",'%S')
        self.module_name_entry = tk.Entry(self.root,width=4,validate="key", validatecommand=vcmd)
        self.module_name_entry.delete(0,"end")
        self.module_name_entry.insert(0,"A1")

        text_weight_entry=tk.StringVar()
        text_weight_entry.set("Enter Weight of Net:")
        self.label_weight_entry = tk.Label(self.root, textvariable=text_weight_entry, height=1)
        vcmd2 = (self.root.register(self.validate_weight), "%d",'%S')
        self.module_weight_entry = tk.Entry(self.root,width=3,validate="key", validatecommand=vcmd2)
        self.module_weight_entry.delete(0,"end")
        self.module_weight_entry.insert(0,"1")

        self.text_cost_val = tk.StringVar()
        self.text_cost_val.set("0")
        self.label_cost_val = tk.Label(self.root,textvariable=self.text_cost_val,height=1)
        
        self.text_cost = tk.StringVar()
        self.text_cost.set("Cost:")
        self.label_cost = tk.Label(self.root,textvariable=self.text_cost,height=1)

        self.description = ScrolledText(self.root,bg='white',relief="groove",height=5,width=20,font='TkFixedFont')

        #setup events
        self.key_del_event = self.root.bind("<Delete>",self.keyDel)
        self.cut_net_event = self.root.bind("t",self.togget_net)

        self.mouse_drag_event = self.canv.bind("<B1-Motion>",self.mouseDrag)
        self.double_left_click_event = self.canv.bind("<Double-Button-1>",self.doubleLeftClick)
        self.left_click_event = self.canv.bind("<Button-1>",self.leftClick)

        #setup pack for widgets
        self.label_cost.pack(in_=self.left_frame)
        self.label_cost_val.pack(in_=self.left_frame)
        self.label_weight_entry.pack(in_=self.left_frame)
        self.module_weight_entry.pack(in_=self.left_frame)
        self.label_module_entry.pack(in_=self.left_frame)
        self.module_name_entry.pack(in_=self.left_frame)
        self.create_module_btn.pack(in_=self.left_frame)

        self.clear_log_btn.pack(in_=self.bottom_right_frame,side="right",anchor="center")

        self.controls_txt = 'Controls: "DEL" to delete when highlighted, "t" to toggle net when highlighted, double click to connect \n'

        self.description.tag_config('error', foreground='red')
        self.description.tag_config('msg', foreground='green')

        self.clearLog()

        self.canv.pack(in_=self.top_right_frame,fill = "both",expand=True)
        self.description.pack(in_=self.bottom_right_frame,fill="x",expand=True)

        self.root.after(self.redraw_time,self.update)

        self.file_types = [('Data Files', '*.dat'),  
                ('All Files', '*.*')]
    
        self.net_list = netlist(self.canv)

        self.sim_sa = None
        self.sim_sa_ui = None

    def addToText(self,txt,tag):
        self.description.config(state="normal")
        self.description.insert(tk.INSERT,txt + "\n",tag)
        self.description.see("end")
        self.description.config(state="disabled")


    def clearLog(self):
        self.description.config(state="normal")
        self.description.delete('1.0', tk.END)
        self.description.insert(tk.INSERT,self.controls_txt,"msg")
        self.description.config(state="disabled")

    def on_closing(self):
        self.kill = True

    def runSimulatedAnnealingUI(self):
        #check for atleast two modules and one net
        if(len(self.net_list.returnListofNets()) > 0):
            tmp_file = "./tmp_org_sa_sim.dat"
            self.genNetlist(tmp_file)
            sa_setting_ui(tmp_file,False,self.root)
        else:
            messagebox.showerror("Error", "Current netlist must contain atleast one net")
        
    def importNetlist(self):
        path = filedialog.askopenfilename(initialdir="./")
        if(path):
            tag_list = ["UI"]
            ui_str = self.net_list.importNetlist(path,tag_list)
            for row in ui_str:
                if(row[0]=="UI"):
                    if(row[1]=="cwh"): #canvas width,height
                        self.canv.config(width=int(row[2]),height=int(row[3]))
                    if(row[1]=="rwg"):
                        self.root.config(width=int(row[2]),height=int(row[3]))
                        self.root.update()

            
    def genNetlist(self,path=None):
        if(path==None):
            path = filedialog.asksaveasfile(mode='w',filetypes=self.file_types,defaultextension=self.file_types[0],initialdir="./")
            if(path):
                path = path.name

        if(path):
            canv_w = self.canv.winfo_width()
            canv_h=  self.canv.winfo_height()
            ui_str_canv = "UI,cwh,"+ str(canv_w) + "," + str(canv_h) #save canv width and height
            roor_w = self.root.winfo_width
            root_h = self.root.winfo_height
            ui_str_root =  "UI,rwh,"+ str(roor_w) + "," + str(root_h) #save root width and height
            str_list = []
            str_list.append(ui_str_root)
            str_list.append(ui_str_canv)
            self.net_list.saveNetlist(path,str_list)

    def validate_weight(self,d,S):
        if(d=='1'): #something inserted
            if(len(self.module_weight_entry.get())<2): #allow three letter max
                for ch in S:
                    if(ch.isdigit()==False):
                        return False
                return True
            else:
                return False
        else:
            return True

    def validate_name(self,d,S):
        if(d=='1'): #something inserted
            if(len(self.module_name_entry.get())<3): #allow three letter max
                for ch in S:
                    if(ch.isdigit()==False and (ch.isalpha()==False)):
                        return False
                return True
            else:
                return False
        else:
            return True

    def createModule(self): #module follows cursor until button clicked
        if(self.new_module_active==False):
            name_str = self.module_name_entry.get()
            if(len(name_str)>0):
                for _module in self.net_list.adj_list:
                    if(_module.name==name_str):
                        print("Error: Enter Unique Module Name")
                        self.addToText("Error: Enter Unique Module Name","error")
                        return
                self.new_module = module(self.canv,name_str,0,0)
                self.net_list.addModule(self.new_module)
                if(name_str[-1].isdigit()):
                    value = 1
                    if(name_str[-2].isdigit()):
                        value_str = name_str[-2] + name_str[-1]
                        value += int(value_str)
                        name_str = name_str[0] + str(value)
                    else:
                        value_str = name_str[-1]
                        value += int(value_str)
                        if(name_str[1].isalpha()):
                            name_str = name_str[0] + name_str[1] + str(value)
                        else:
                            name_str = name_str[0] + str(value)
                    
                    if(value < 100):
                        self.module_name_entry.delete(0,"end")
                        self.module_name_entry.insert(0,name_str)
                    
                self.new_module_active = True
            else: 
                print("Error: Enter Module Name")
                self.addToText("Error: Enter Module Name","error")


    def leftClick(self,event): #handle case of placing new module
        if(self.new_module_active==True):
            self.new_module_active = False

    def doubleLeftClick(self,event): # Handle connecting of two modules
        if(self.new_module_active==False):
            xy = self.getCursorXY()
            if(self.module_1_selected==None): #no module currently selected 
                self.module_1_selected = self.net_list.getModuleAtPos(xy[0],xy[1])
            else:
                self.module_2_selected = self.net_list.getModuleAtPos(xy[0],xy[1])
                if(self.module_2_selected==None): #clicked on blank area clear selection
                    self.module_1_selected = None 
                else: #two diffrent modules are selected so create a net between the two
                    if(self.module_weight_entry.get().isdigit()):
                        status = self.net_list.addNet(net(self.canv,self.module_1_selected,self.module_2_selected,int(self.module_weight_entry.get())))
                        if(status==True): #check if connection was successful
                            self.module_1_selected = None
                        self.module_2_selected = None
                    else:
                        print("Error: Enter Weight")
                        self.addToText("Error: Enter Weight","error")


    def togget_net(self,evet):
        xy = self.getCursorXY()
        self.net_list.toggleNetAtPos(xy[0],xy[1])
    
    def getCursorXY(self):
        x = self.root.winfo_pointerx() - self.canv.winfo_rootx()
        y = self.root.winfo_pointery() - self.canv.winfo_rooty()
        if(x < 0):
            x = 0
        if(y < 0):
            y = 0
        if(x > self.canv.winfo_width()):
            x = self.canv.winfo_width()
        if(y > self.canv.winfo_height()):
            y = self.canv.winfo_height()
        return x,y

    def keyDel(self,event):
        if(self.new_module_active==False):
            xy = self.getCursorXY()
            if(self.module_1_selected==None or (self.net_list.getModuleAtPos(xy[0],xy[1])!=self.module_1_selected and self.net_list.getModuleAtPos(xy[0],xy[1])!=self.module_2_selected)): #do not allow double clicked module to be deleted
                self.net_list.deleteInstanceAtPos(xy[0],xy[1])

    def mouseDrag(self,event):
        self.drag_active = True
        
    def update(self):
        self.text_cost_val.set(str(self.net_list.cost))
        if(self.kill==True):
            self.root.destroy()
            return
        xy = self.getCursorXY() 
        if(self.new_module_active==True):
            self.new_module.redrawAtNewPos(xy[0],xy[1],"green")
        
        else:
            self.net_list.redrawWithHighlight(xy[0],xy[1])
            if(self.drag_active==True):
                self.drag_active = False
                _module = self.net_list.getModuleAtPos(xy[0],xy[1])
                if(_module!=None):
                    _module.redrawAtNewPos(xy[0],xy[1],"green")
        
            if(self.module_1_selected!=None):
                self.module_1_selected.redraw("red")
        self.root.update()
        self.update_job = self.root.after(self.redraw_time,self.update)

class display_ui:

    def __init__(self,root,canv_width,canv_height,file_menu_active = False, net_list_path = None,msg=""):
        self.root = tk.Toplevel(root)
        
        self.net_list = None
        self.redraw_time = 1
        self.x = 0
        self.y = 0
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.allow_kill = False

        self.menubar = tk.Menu(self.root)
        self.filemenu = tk.Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Generate Netlist", command=self.genNetlist)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.root.config(menu=self.menubar)

        if(file_menu_active):
            self.menubar.entryconfig("File", state="normal")
        else:
            self.menubar.entryconfig("File", state="disabled")
    
        self.top_frame = tk.Frame(self.root)
        self.bottom_frame = tk.Frame(self.root)

        self.top_frame.pack(side = "top",fill="both",expand=True)
        self.bottom_frame.pack(side='bottom',fill = "x")

        self.description = ScrolledText(self.root,bg='white',relief="groove",height=5,width=20,font='TkFixedFont')
        self.canv = tk.Canvas(self.root, bg="gray10", width=canv_width, height=canv_height)

        self.description.pack(in_=self.bottom_frame,fill="x",expand=True)
        self.canv.pack(in_ =self.top_frame,fill = "both",expand=True)

        self.file_types = [('Data Files', '*.dat'),  
                ('All Files', '*.*')]

        self.net_list = netlist(self.canv)
        if(net_list_path!=None):
            self.importNetlist(net_list_path)

    def changeTxt(self,txt):
        self.description.config(state="normal")
        self.description.delete('1.0', tk.END)
        self.description.insert(tk.INSERT,txt)
        self.description.config(state="disabled")

    def activateMenuBar(self):
        self.menubar.entryconfig("File", state="normal")

    def deactivateMenuBar(self):
        self.menubar.entryconfig("File", state="disabled")

    def on_closing(self):
        if(self.allow_kill):
            self.root.destroy()

    def importNetlist(self,path):
        if(path):
          self.net_list.importNetlist(path)

    def genNetlist(self):
        path = filedialog.asksaveasfile(mode='w',filetypes=self.file_types,defaultextension=self.file_types[0],initialdir="./")
        if(path):
            canv_w = self.canv.winfo_width()
            canv_h=  self.canv.winfo_height()
            ui_str_canv = "UI,cwh,"+ str(canv_w) + "," + str(canv_h) #save canv width and height
            roor_w = self.root.winfo_width
            root_h = self.root.winfo_height
            ui_str_root =  "UI,rwh,"+ str(roor_w) + "," + str(root_h) #save root width and height
            str_list = []
            str_list.append(ui_str_root)
            str_list.append(ui_str_canv)
            self.net_list.saveNetlist(path,str_list)

    def getCursorXY(self):
        x = self.root.winfo_pointerx() - self.canv.winfo_rootx()
        y = self.root.winfo_pointery() - self.canv.winfo_rooty()
        if(x < 0):
            x = 0
        if(y < 0):
            y = 0
        if(x > self.canv.winfo_width()):
            x = self.canv.winfo_width()
        if(y > self.canv.winfo_height()):
            y = self.canv.winfo_height()
        return x,y


    def update(self):
        self.net_list.redrawWithHighlight()
        self.root.update()

class sa_setting_ui:
    def __init__(self,net_list_path,isrootwindow = True, root = None):
        
        self.net_list_path = net_list_path
        if(isrootwindow):
            self.root = tk.Tk()
        else:
            self.root = tk.Toplevel(root)
            self.root.grab_set()
        

        self.root.title("Simulated Annealing Properties")
        self.root.geometry("500x600")
        self.root.resizable(False, False)

        vcmd = (self.root.register(self.validate_entry), "%d",'%S')

        self.alpha_entry = tk.Entry(self.root,width=10,validate="key", validatecommand=vcmd)
        self.start_temp_entry = tk.Entry(self.root,width=10,validate="key", validatecommand=vcmd)
        self.end_temp_entry = tk.Entry(self.root,width=10,validate="key", validatecommand=vcmd)
        self.kb_entry = tk.Entry(self.root,width=10,validate="key", validatecommand=vcmd)

        text_alpha_entry=tk.StringVar()
        text_alpha_entry.set("\u03B1(%):")
        self.label_alpha_entry = tk.Label(self.root, textvariable=text_alpha_entry, height=1)

        text_start_temp=tk.StringVar()
        text_start_temp.set("T(start):")
        self.label_start_temp_entry = tk.Label(self.root, textvariable=text_start_temp, height=1)

        text_end_temp=tk.StringVar()
        text_end_temp.set("T(stop):")
        self.label_end_temp_entry = tk.Label(self.root, textvariable=text_end_temp, height=1)

        text_kb =tk.StringVar()
        text_kb.set("k:")
        self.label_kb_set = tk.Label(self.root, textvariable=text_kb, height=1)
   
        text_choice =tk.StringVar()
        text_choice.set("Problem:")
        self.label_drop_menu = tk.Label(self.root, textvariable=text_choice, height=1)
           
        text_log_path =tk.StringVar()
        text_log_path.set("Log Path:")
        self.label_log_path = tk.Label(self.root, textvariable=text_log_path, height=1)

        self.log_path_entry = tk.Entry(self.root,width=10)
        
        self.text_label_error =tk.StringVar()
        self.text_label_error.set("")
        self.label_error = tk.Label(self.root, textvariable=self.text_label_error, height=1,fg="red")

        self.run_sim_btn = tk.Button(self.root,text="Run Solver", command=self.runSolver)
        self.sel_path_btn = tk.Button(self.root,text="...",command=self.selPath)
        self.log_path_entry.config(state='disabled') 

        self.kill_sim_btn = tk.Button(self.root,text="Kill Sim", command=self.killSim)
        self.kill_sim_btn.config(state="disabled")

        self.description = ScrolledText(self.root,bg='white',relief="groove",height=10,width=50,font='TkFixedFont')


        self.selected = tk.StringVar(self.root)
        self.selected.trace("w",self.changeChoice)
        self.choices = { 'Partitioning','Travelling Salesman'}
        self.selected.set('Partitioning') # set the default option
        self.drop_menu = tk.OptionMenu(self.root, self.selected, *self.choices)

        self.show_sim_active = IntVar()
        self.show_sim_active.set(1)
        self.show_sim_btn = tk.Checkbutton(self.root,text = "Show Live Sim", variable = self.show_sim_active, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 20)

        self.log_active = IntVar()
        self.log_active.trace("w",self.saveLog)

        self.log_active.set(1)
        self.log_active_btn = tk.Checkbutton(self.root,text = "Save Log", variable = self.log_active, \
                 onvalue = 1, offvalue = 0, height=1, \
                 width = 10)


        self.alpha_entry.place(relx=0.5, rely=0.03, anchor="w")
        self.label_alpha_entry.place(relx=0.4, rely=0.03, anchor="e")

        self.start_temp_entry.place(relx=0.5, rely=0.105, anchor="w")
        self.label_start_temp_entry.place(relx=0.4, rely=0.105, anchor="e")
    
        self.end_temp_entry.place(relx=0.5, rely=0.18, anchor="w")
        self.label_end_temp_entry.place(relx=0.4,rely=0.18,anchor="e")

        self.kb_entry.place(relx=0.5, rely=0.255, anchor="w")
        self.label_kb_set.place(relx=0.4, rely=0.255, anchor="e")

        self.drop_menu.place(relx=0.5,rely=0.33,anchor="w")
        self.label_drop_menu.place(relx=0.4,rely=0.33,anchor="e")

        self.sel_path_btn.place(relx=0.62,rely=0.405,anchor="w")
        self.label_log_path.place(relx=0.4,rely=0.405,anchor="e")
        self.log_path_entry.place(relx=0.5,rely=0.405,anchor="w")
        self.log_active_btn.place(relx=0.675,rely=0.405,anchor="w")

        self.description.place(relx=0.5,rely=0.7,anchor="center")


        self.label_error.place(relx=0.5,rely=0.875,anchor="center")
        self.run_sim_btn.place(relx=0.5, rely=0.95, anchor="center")
        self.kill_sim_btn.place(relx=0.25,rely=0.95,anchor="center")

        self.show_sim_btn.place(relx=0.675, rely=0.1425, anchor="w")

        self.alpha_entry.delete(0,"end")
        self.alpha_entry.insert(0,"95")

        self.start_temp_entry.delete(0,"end")
        self.start_temp_entry.insert(0,"100")

        self.end_temp_entry.delete(0,"end")
        self.end_temp_entry.insert(0,"1")

        self.kb_entry.delete(0,"end")
        self.kb_entry.insert(0,"1")

        self.kill_sim = False

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.root.update()

    def on_closing(self):
        tmp = "./tmp.dat"
        if (os.path.isfile(self.net_list_path)):
            os.remove(self.net_list_path)

        if (os.path.isfile(tmp)):
            os.remove(tmp)

        self.root.destroy()

    def saveLog(self,*args):
        self.log_path_entry.config(state='normal') 
        self.log_path_entry.delete(0,tk.END)
        self.log_path_entry.config(state='disabled') 
        if(self.log_active.get()==1):
            self.sel_path_btn.config(state='normal')
        else:
            self.sel_path_btn.config(state='disabled')
            

    def selPath(self):
        path = filedialog.askdirectory(initialdir="./")
        self.log_path_entry.config(state='normal') 
        self.log_path_entry.delete(0,tk.END)
        self.log_path_entry.insert(0,path)
        self.log_path_entry.config(state='disabled') 

    def killSim(self):
        self.kill_sim_btn.config(state="disabled")
        self.kill_sim = True
        self.sim_sa.stop = True

    def validate_entry(self,d,S):
        if(d=='1'): #something inserted
            for ch in S:
                if(ch.isdigit()==False):
                    return False
            return True
        else:
            return True

    def runSolver(self):
        self.kill_sim = False
        alpha = float(self.alpha_entry.get())
        t_start = float(self.start_temp_entry.get())
        t_end = float(self.end_temp_entry.get())
        kb = float(self.kb_entry.get())
        log_path = self.log_path_entry.get()

        if(self.log_active.get()):
            if(os.path.isdir(log_path)==False):
                self.text_label_error.set("Log Path is Invalid")
                return
        else:
            log_path = None

        if(alpha >= 100 or alpha <= 0):
            self.text_label_error.set("\u03B1 invalid, must be between (0,100)")
            return
        if(t_end > t_start):
            self.text_label_error.set("T(start) must be greater than T(end)")
            return
        
        tag = ["UI"]
 
        ui_str = utility.returnTagListFromNetlistPath(self.net_list_path,tag)
        canv_width = 500
        canv_height = 500
        for row in ui_str:
            if(row[0]=="UI"):
                if(row[1]=="cwh"): #canvas width,height
                    canv_width = int(row[2])
                    canv_height = int(row[3])

        self.sim_sa_ui = display_ui(self.root,canv_width,canv_height)
        self.run_sim_btn.config(state="disabled")
        self.kill_sim_btn.config(state="normal")

        self.text_label_error.set("")

        if(self.selected.get()=="Partitioning"):
            self.sim_sa = saPartitionSolver(self.net_list_path,(alpha/100),t_start,t_end,kb,log_path)   
            if(self.show_sim_active.get()):     
                self.runSimulatedAnnealingPartitionItr()
            else:
                self.runSimulatedAnnealingPartition()
        else:
            self.sim_sa_ui.root.destroy()
            self.runSimulatedAnnealingTS()

    def runSimulatedAnnealingTS(self):
        self.run_sim_btn.config(state="normal")
        self.kill_sim_btn.config(state="disabled")
        messagebox.showwarning("Warning", "Work in Progress")

    def runSimulatedAnnealingPartitionItr(self):
        if(self.kill_sim ==True):
            self.run_sim_btn.config(state="normal")
            self.sim_sa_ui.root.destroy()
            return
        tmp_file = "./tmp.dat"
        cost,accepted,fin,reason,set1,set2 = self.sim_sa.runNextIteration(tmp_file)
        self.sim_sa_ui.importNetlist(tmp_file)
        self.sim_sa_ui.update()

        setA = "SetA = {"
        for _module in set1:
            setA += _module.name + " , "
        setA += " }"

        setB = "SetB = {"
        for _module in set2:
            setB += _module.name + " , "
        setB += " }"

        if(fin):
            self.run_sim_btn.config(state="normal")
            self.sim_sa_ui.changeTxt("Cost: " + str(cost) + "\n" + "Final Solution" + "\n" + setA + "\n" + setB)
            self.sim_sa_ui.activateMenuBar()
            self.sim_sa_ui.allow_kill = True
            self.kill_sim_btn.config(state="disabled")
            return
        if(accepted):
            self.sim_sa_ui.changeTxt("Cost: " + str(cost) + "\n" + "Solution Accepted" + "\n" + "Reason: " + reason + "\n" + setA + "\n" + setB)
        else:
            self.sim_sa_ui.changeTxt("Cost: " + str(cost) + "\n" + "Solution Rejected" +  "\n" + "Reason: " + reason + "\n" + setA + "\n" + setB )

        self.root.after(1000,self.runSimulatedAnnealingPartitionItr)

    def runSimulatedAnnealingPartition(self):
        tmp_file = "./tmp.dat"
        self.sim_sa_ui.changeTxt("SIM RUNNING")

        cost,set1,set2 = self.sim_sa.runUntilComplete(tmp_file)

        self.run_sim_btn.config(state="normal")
        if(self.kill_sim==True):
            self.sim_sa_ui.root.destroy()
            return

        setA = "SetA = {"
        for _module in set1:
            setA += _module.name + " , "
        setA += " }"

        setB = "SetB = {"
        for _module in set2:
            setB += _module.name + " , "
        setB += " }"

        self.sim_sa_ui.importNetlist(tmp_file)
        self.sim_sa_ui.update()
        self.sim_sa_ui.changeTxt("Cost: " + str(cost) + "\n" + "Final Solution" + "\n" + setA + "\n" + setB)
        self.sim_sa_ui.activateMenuBar()
        self.kill_sim_btn.config(state="disabled")
        self.sim_sa_ui.allow_kill = True

    def changeChoice(self,*args):
        self.description.config(state="normal")
        self.description.delete('1.0',tk.END)
        sa_str = "P = exp(-\u0394/k*T)"
        sa_str += "\nT = \u03B1*T'"
        if(self.selected.get()=="Partitioning"):
            sa_str += "\nIn Partitioning the solver will attempt to evenly divde the modules in the netlist into two seperatesets (setA and setB) by cutting nets. The sets aredecided by minimzing the total cutting cost required. The cost to cut a net is dictated by it's weight."
            self.description.insert(tk.INSERT,sa_str)
        else:
            sa_str += "\nIn Traveling Salesman the solver will attempt to visit all modules in the netlist in a route that minimizes total cost of travel without repeating a visit. The cost to travel from one module to another is dictated by the net's weight that connects the two."
            self.description.insert(tk.INSERT,sa_str)

        self.description.config(state="disabled")
