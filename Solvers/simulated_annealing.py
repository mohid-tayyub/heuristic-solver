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

import random
import math
from instances import utility
import copy 
from instances import netlist
import datetime as dt

class saPartitionSolver: #class for simulated annealing partitioner solver
    
    def __init__(self,netlist_path,alpha,intial_temp,stop_temp,kb=1,log_path = None):

        self.itr = 0

        if(log_path!=None):
            self.create_log = True
            self.log_path = log_path
        else:
            self.create_log = False

        self.createLog()

        self.net_list = netlist(None)
        self.net_list.importNetlist(netlist_path)
        self.net_list.connectAllNets()
        self.alpha = alpha
        self.intial_temp = intial_temp
        self.current_temp = intial_temp
        self.stop_temp = stop_temp
        self.kb = kb
        self.current_set1 = []
        self.current_set2 = []
        self.current_cost = None
        self.current_cut_nets = []
        self._initIntialSets()
        self.stop = False
    
    def createLog(self):
        if(self.create_log==True):
            time_stamp = dt.datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
            self.log_file_path = self.log_path + "/" + "SIMSA" + "_" + time_stamp + ".csv"
            self.log_file = open(self.log_file_path, "w")
            header = "Iteration,Cost,SetA,SetB,Solution Accepted,U,P,Reason"
            self.log_file.write(header + "\n")
            self.log_file.close()

    def addToLog(self,itr,cost,setA,setB,accepted,U,P,reason):
        if(self.create_log):
            self.log_file = open(self.log_file_path, "a")
            self.log_file.write(str(itr) + "," + str(cost) + ",")
            for _module in setA:
                self.log_file.write(_module.name + "-")
            self.log_file.write(",")
            for _module in setB:
                self.log_file.write(_module.name + "-")

            self.log_file.write( "," + str(accepted) + "," + str(U)  + ","  + str(P) + ","  + reason)
            self.log_file.write("\n")
            self.log_file.close()

    def _initIntialSets(self):
        self.itr = 0
        module_list = []
        for module in self.net_list.adj_list:
            module_list.append(module)
        random.shuffle(module_list)
        size = len(module_list)
        mid_id = int(size/2)
        self.current_set1 = module_list[:mid_id]
        self.current_set2 = module_list[mid_id:]
        self.current_cut_nets,self.current_cost = utility.determineCutNets(self.current_set1,self.current_set2,self.net_list)
        self.net_list.cutNets(self.current_cut_nets)
        self.addToLog(self.itr,self.current_cost,self.current_set1,self.current_set2,True,-1,-1,"Init")
        self.itr += 1


    def reset(self):
        self.current_temp = self.intial_temp
        self.create_log()
        self._initIntialSets()

    def runUntilComplete(self,save_path):
        self.stop = False
        
        while(self.current_temp > self.stop_temp):
            if(self.stop==True):
                return None
            self._runNextIteration()

        self.addToLog(self.itr,self.current_cost,self.current_set1,self.current_set2,True,-1,-1,"Final Solution")
        utility.saveNewNetlist(self.net_list,self.current_cut_nets,save_path)
        return self.current_cost,self.current_set1,self.current_set2 

    def runNextIteration(self,save_path): #run a single iteration and return results
        cut_nets = []
        accepted = True
        fin = True
        reason = ""
        if(self.current_temp > self.stop_temp): #stop condition not met, run another iteration
            fin = False
            cut_nets,cost,accepted,reason,tmp_set1,tmp_set2 = self._runNextIteration()
            utility.saveNewNetlist(self.net_list,cut_nets,save_path)
            return cost,accepted,fin,reason,tmp_set1,tmp_set2
        else:
            self.addToLog(self.itr,self.current_cost,self.current_set1,self.current_set2,True,-1,-1,"Final Solution")
            utility.saveNewNetlist(self.net_list,self.current_cut_nets,save_path)
            return self.current_cost,accepted,fin,reason,self.current_set1,self.current_set2 

    def _runNextIteration(self):
        reason = ""
        tmp_set1 = copy.copy(self.current_set1)
        tmp_set2 = copy.copy(self.current_set2)

        idx1 = random.randrange(len(tmp_set1))
        idx2 = random.randrange(len(tmp_set2))

        tmp_set1[idx1],tmp_set2[idx2] = tmp_set2[idx2],tmp_set1[idx1]

        tmp_cut_nets,tmp_cost = utility.determineCutNets(tmp_set1,tmp_set2,self.net_list)

        accept = False
        rnd = -1
        p = -1
        if(tmp_cost < self.current_cost):
            reason = "New Cost < Old Cost"
            self.current_set1 = tmp_set1
            self.current_set2 = tmp_set2
            self.current_cost = tmp_cost
            self.current_cut_nets = tmp_cut_nets
            accept = True
        else:
            delta = tmp_cost - self.current_cost
            p = math.exp(-1*(delta/(self.kb*self.current_temp)))
            rnd = random.uniform(0, 1)
            if(rnd < p): #accept worse solution 
                accept = True 
                reason = "New Cost > Old Cost & P > U(0-1)"
                self.current_set1 = tmp_set1
                self.current_set2 = tmp_set2
                self.current_cost = tmp_cost
                self.current_cut_nets = tmp_cut_nets
            else:
                reason = "New Cost > Old Cost & P < U(0-1)"
                accept = False

        self.addToLog(self.itr,tmp_cost,tmp_set1,tmp_set2,accept,rnd,p,reason)
        self.itr += 1

        self.current_temp *= self.alpha
        return tmp_cut_nets,tmp_cost,accept,reason,tmp_set1,tmp_set2

