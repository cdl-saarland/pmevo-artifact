# vim: et:ts=4:sw=4:fenc=utf-8

from abc import ABC, abstractmethod
from typing import *

from gurobipy import *

from utils.architecture import Architecture, Insn, Port
from utils.experiment import Experiment
from .sim_processor import SimProcessor

class LPProcessor(SimProcessor):
    """ Simulation processor using an LP solved by Gurobi for computing cycle
        numbers.
    """
    def __init__(self, mapping: Mapping):
        super().__init__(mapping)

    def get_description(self):
        return "simulation processor using an LP solved by Gurobi"

    def cycles_for_weights(self, weights):
        P = self.arch.port_list()

        m = Model("schedule")
        m.setParam('OutputFlag', 0)

        x_vars = m.addVars([(i, k)
            for i in weights.keys() for k in P], name="x")

        lat = m.addVar(name="latency", obj=1.0)

        m.addConstrs(( quicksum([ x_vars[(i, k)] for k in P ]) == n
            for i, n in weights.items()))

        m.addConstrs(( quicksum([ x_vars[(i, k)] for i in weights.keys() ]) <= lat
            for k in P))

        m.addConstrs((x_vars[(i, k)] == 0
            for i in weights.keys() for k in P if (self.uop2bv((k,)) & i) == 0 ))

        m.optimize()

        assert(m.status == GRB.Status.OPTIMAL)

        return m.objVal

