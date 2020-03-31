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

import copy
import os
import csv

class net:
    def __init__(self,canv,module1,module2,weight,normal = True): #normal is paramater the determines if the net is standard = True or selected = False, non normal (selected) net implies the net is cut,chosen,etc and therefore plays a role in the netlist cost
        self.normal = normal
        if(self.normal==True):
            self.line_color = "gray64"
        else:
            self.line_color = "red"
        self.circle_size = 10
        self.line_width = 3
        self.canv = canv
        self.weight = weight
        self.module1 = module1
        self.module2 = module2
        self.line = None 
        self.circle = None 
        self.txt = None 

    def getOverlapCase(self):
        bbox1 = self.module1.getBbox()
        bbox2 = self.module2.getBbox()
        if(bbox2[0] < bbox1[2] and bbox2[2] > bbox1[0]):
            if(bbox2[3] < bbox1[1]): #case 1 draw line from bottom middle (box2) to top middle (box1)
                return 1
            else:  #case 2 draw line from top middle (box2) to bottom middle (box1)
                return 2
        else:
            if(bbox2[0] > bbox1[2]): #case 3 draw line from left middle (box2) to right middle (box1)
                return 3
            else:  #case 4 draw line from right middle (box2) to left middle (box1)
                return 4

    def getP1toP2(self): #based on current case calcuate the coordinates of the two points to draw line between
        case = self.getOverlapCase()
        bbox1 = self.module1.getBbox()
        bbox2 = self.module2.getBbox()
        if(case==1):
            x1 = self.module1.x
            x2 = self.module2.x
            y1 = bbox1[1]
            y2 = bbox2[3]
        elif(case==2):
            x1 = self.module1.x
            x2 = self.module2.x
            y1 = bbox1[3]
            y2 = bbox2[1]
        elif(case==3):
            y1 = self.module1.y
            y2 = self.module2.y
            x1 = bbox1[2]
            x2 = bbox2[0]
        else:
            y1 = self.module1.y
            y2 = self.module2.y
            x1 = bbox1[0]
            x2 = bbox2[2]
        xy = x1,y1,x2,y2
        return xy

    def redraw(self,color="white"): #update postion based on new modules coord and redraw 
        if(self.normal==True):
            self.line_color = "gray64"
        else:
            self.line_color = "red"
        if(self.line!=None):
            self.canv.delete(self.line)
            self.canv.delete(self.circle)
            self.canv.delete(self.txt)
        self.line = self.canv.create_line(self.getP1toP2(),fill=self.line_color,width=self.line_width)
        self.circle = self.canv.create_oval(self.getOvalPos(),fill=color)
        self.txt = self.canv.create_text(self.getMidPos(),text=str(self.weight),fill = "black")
    
    def getMidPos(self): #get the position to the middle of drawn line
        xy = self.getP1toP2()
        xoffset = abs((xy[2] - xy[0]) / 2)
        yoffset = abs((xy[3] - xy[1]) / 2)
        if(xy[0] < xy[2]):
            x = xy[0] + xoffset
        else:
            x = xy[2] + xoffset
        if(xy[1] < xy[3]):
            y = xy[1] + yoffset
        else:
            y = xy[3] + yoffset
        return x,y

    def getOvalPos(self):
        xy = self.getMidPos()
        x1 = xy[0] - self.circle_size
        y1 = xy[1] - self.circle_size
        x2 = xy[0] + self.circle_size
        y2 = xy[1] + self.circle_size
        return x1,y1,x2,y2

    def inBbox(self,x,y): #Oval is in a tight BBOX, check if x,y coord inside boundedbox
        bbox = self.getOvalPos()
        if(x >= bbox[0] and y >= bbox[1] and x <= bbox[2] and y <= bbox[3]):
            return True 
        else:
            return False

    def clear(self):
        self.canv.delete(self.line)
        self.canv.delete(self.circle)
        self.canv.delete(self.txt)


class module:
    def __init__(self,canv,name,init_x,init_y,color="white"):
        self.default_color = color
        self.width = 30
        self.height = 30
        self.x = init_x
        self.y = init_y
        self.name = name
        self.canv = canv
        self.rect = None #canv.create_rectangle(self.getBbox(),fill="white")
        self.txt = None #canv.create_text(init_x,init_y,text=name,fill = "black")

    def getBbox(self):
        x1 = self.x - (self.width/2)
        y1 = self.y - (self.height/2)
        x2 = self.x + (self.width /2)
        y2 = self.y + (self.height/2)
        bbox = x1,y1,x2,y2
        return bbox

    def redrawAtNewPos(self,new_x,new_y,color=None): #delete and redraw to new coord
        if(color==None):
            color = self.default_color
        self.canv.delete(self.rect)
        self.canv.delete(self.txt)
        self.x = new_x
        self.y = new_y
        self.rect = self.canv.create_rectangle(self.getBbox(),fill=color)
        self.txt = self.canv.create_text(self.x,self.y,text=self.name,fill = "black")

    def redraw(self,color=None):
        if(color==None):
            color = self.default_color
        if(self.rect!=None):
            self.canv.delete(self.rect)
            self.canv.delete(self.txt)
        self.rect = self.canv.create_rectangle(self.getBbox(),fill=color)
        self.txt = self.canv.create_text(self.x,self.y,text=self.name,fill = "black")

    def inBbox(self,x,y): #is requested x,y coord inside boundedbox
        bbox = self.getBbox()
        if(x >= bbox[0] and y >= bbox[1] and x <= bbox[2] and y <= bbox[3]):
            return True
        else:
            return False

    def clear(self):
        self.canv.delete(self.rect)
        self.canv.delete(self.txt)

class netlist:
    def __init__(self,canv):
        self.cost = 0
        self.adj_list = {}
        self.canv = canv

    def addModule(self,module):
        self.adj_list[module] = []

    def addNet(self,net): #If no duplicates then attach
        if(net.module1==net.module2): #selected same module
            return False
        for _net in self.returnListofNets():
            if( (_net.module1==net.module1 and _net.module2==net.module2) or (_net.module2==net.module1 and _net.module1==net.module2) ):
                return False
        if(net.normal==False):
            self.cost  += net.weight
        self.adj_list[net.module1].append(net)
        self.adj_list[net.module2].append(net)
        return True

    def getModuleAtPos(self,x,y): #check if there is a module at requested position
        for module in self.adj_list:
            if(module.inBbox(x,y)==True):
                return module
        return None

    def toggleNetAtPos(self,x,y):
        for _net in self.returnListofNets():
            if(_net.inBbox(x,y)==True):
                _net.normal = not(_net.normal)
                if(_net.normal==False):
                    self.cost  += _net.weight
                else:
                    self.cost  -= _net.weight
                break
            
    def deleteInstanceAtPos(self,x,y): #delete any instance (if exists) at requested position (module or net)
        for _module in self.adj_list:
            if(_module.inBbox(x,y)==True):  #if module at position delete module and all nets connected to module
                _module.clear()
                nets = self.adj_list.pop(_module, None)
                for _net in nets: #clear nets and delete connection in adj list
                    if(_net.normal==False):
                        self.cost  -= _net.weight
                    _net.clear()
                    if(_net.module1 in self.adj_list):
                        self.adj_list[_net.module1][:] =  [x for x in self.adj_list[_net.module1] if (x != _net)]
                    if(_net.module2 in self.adj_list):
                        self.adj_list[_net.module2][:] =  [x for x in self.adj_list[_net.module2] if (x != _net)]
                return
        for _net in self.returnListofNets():
            if(_net.inBbox(x,y)==True): #if net at position delete connection and update adj_list
                if(_net.normal==False):
                        self.cost  -= _net.weight
                _net.clear()
                self.adj_list[_net.module1][:] =  [x for x in self.adj_list[_net.module1] if (x != _net)]
                self.adj_list[_net.module2][:] =  [x for x in self.adj_list[_net.module2] if (x != _net)]
                return
    
    def clear(self):
        for _module in self.adj_list:
            _module.clear()
        for _net in self.returnListofNets():
            _net.clear()
        self.adj_list = {}

    def cutNets(self,cut_net_list):
        for _net in self.returnListofNets():
            if(_net in cut_net_list):
                if (_net.normal == True):
                    self.cost += _net.weight
                _net.normal = False
    
    def connectNets(self,connect_net_list):
        for _net in self.returnListofNets():
            if(_net in connect_net_list):
                if (_net.normal == False):
                    self.cost -= _net.weight
                _net.normal = True

    def connectAllNets(self): #activate all nets 
        for _net in self.returnListofNets():
            if (_net.normal == False):
                self.cost -= _net.weight
            _net.normal = True

    def returnListofNets(self):
        nets = []
        tmp_dict = {}
        for _,_nets in self.adj_list.items():
            for _net in _nets:
                if(_net.module1 not in tmp_dict or _net.module2 not in tmp_dict):
                    nets.append(_net)
        return nets

    def redrawWithHighlight(self,x=-1,y=-1): #will redraw all modules and nets, will highligt instances whose BBOX fall within the given x,y
        for module in self.adj_list:
            if(module.inBbox(x,y)==True):
                module.redraw("green")
            else:
                module.redraw()
        for _net in self.returnListofNets():
            if(_net.inBbox(x,y)==True):
                _net.redraw("green")
            else:
                _net.redraw()

    def saveNetlist(self,path,custom_str_list=[]): #saves netlist as well as list of strings in custom_str_list
        f = open(path, "w")
        
        for _str in custom_str_list:
            f.write(_str + "\n")

        for _module in self.adj_list:
            f.write("m," + _module.name + "," + str(_module.x) + "," + str(_module.y) + "," + _module.default_color + "\n")

        for _net in self.returnListofNets():
            f.write("n," + _net.module1.name + "," + _net.module2.name + "," + str(_net.weight) + "," + str(int(_net.normal)) + "\n")

        f.close()

    def importNetlist(self,path,req_tag_list = []): #imports netlist and any return a list of lines with tags in req_tag_list

        self.clear()
        rows = []
        self.cost = 0
        with open(path) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                rows.append(row)
        tmp_dict = {}
        for row in rows:
            if(row[0]=='m'): #add all modules 
                _module = module(self.canv,row[1],int(row[2]),int(row[3]),row[4])
                tmp_dict[_module.name] = _module
                self.addModule(_module)

        for row in rows:
            if(row[0]=='n'): #add all nets
                module1 = tmp_dict.get(row[1])
                module2 = tmp_dict.get(row[2])
                if(module1!=None and module2 != None):        
                    self.addNet(net(self.canv,module1,module2,int(row[3]),int(row[4])))
        tag_str_list = []
        for row in rows:
            if(row[0] in req_tag_list):
                tag_str_list.append(row)
                
        return tag_str_list




class utility:

    @staticmethod
    def determineCutNets(set1_modules,set2_modules,netlist): #determine which nets need to be cut inorder to create two seperate sets and the total cost of THIS cutting
        set1_hash ={}
        set2_hash = {}
        cut_nets = []
        for _module in set1_modules:
            set1_hash[_module] = 1

        for _module in set2_modules:
            set2_hash[_module] = 1

        cost = 0
        for _module in set1_modules:
            nets = netlist.adj_list[_module]
            for _net in nets:
                if( (_net.module1 in set2_hash) or (_net.module2 in set2_hash) ): #this connects a module in set1 to a module in set2 and therefore must be cur
                    cost += _net.weight
                    cut_nets.append(_net)
        return cut_nets,cost

    @staticmethod
    def saveNewNetlist(net_list,cut_nets,save_path): #saves netlist with only nets deactivated in cut_nets
        net_list.connectAllNets()        
        net_list.cutNets(cut_nets)
        net_list.saveNetlist(save_path)

    @staticmethod
    def saySets(set1_modules,set2_modules):
        print("Module1:")
        for _module in set1_modules:
            print (_module.name)
        print("Module2:")
        for _module in set2_modules:
            print (_module.name)

    @staticmethod
    def returnTagListFromNetlistPath(net_list_path,req_tag_list = []):
        rows = []
        with open(net_list_path) as csvfile:
            readCSV = csv.reader(csvfile, delimiter=',')
            for row in readCSV:
                rows.append(row)
        
        tag_str_list = []
        for row in rows:
            if(row[0] in req_tag_list):
                tag_str_list.append(row)
                
        return tag_str_list