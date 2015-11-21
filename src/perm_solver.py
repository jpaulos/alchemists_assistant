import numpy as np
from collections import deque
from itertools import permutations

# color ID numbers
kRed = 0
kGreen = 1
kBlue = 2
kNeutral = 3

class Game:
    def __init__(self):

        # build lookup table of formula mixing results from game data
        self.formula_sign_table = np.zeros((3,8), dtype='bool');
        self.formula_sign_table[0,:] = [0,1,1,0,0,1,0,1];
        self.formula_sign_table[1,:] = [1,0,0,1,0,1,0,1];
        self.formula_sign_table[2,:] = [0,1,0,1,1,0,0,1];
        self.formula_size_table = np.zeros((3,8), dtype='bool');
        self.formula_size_table[0,:] = [0,0,0,0,1,1,1,1];
        self.formula_size_table[1,:] = [0,0,1,1,0,0,1,1];
        self.formula_size_table[2,:] = [1,1,0,0,0,0,1,1];       
        (self.color_table, self.sign_table) = self.BuildColorSignTables()

        # initialize boolean mask over possible game solutions
        n_perms = 8*7*6*5*4*3*2;
        self.mask = np.ones(n_perms, dtype='bool')

    def ComputeColorSign(self,formula_a,formula_b):
        '''Return unique result of mixing formulas (A,B) as (color, sign) pair.
        Computed from formula definitions (slow).
        '''
        matches = 0
        for c in range(0,3):
            if (self.formula_sign_table[c][formula_a] == self.formula_sign_table[c][formula_b]) and (self.formula_size_table[c][formula_a] != self.formula_size_table[c][formula_b]):
                color = c
                sign  = self.formula_sign_table[c][formula_a]
                matches = matches+1
                return (color, sign)
        return (kNeutral, 0)

    def BuildColorSignTables(self):
        '''Build lookup tables for the color and sign of results for binary 
        formula mixtures.
        '''
        color_table = np.zeros((8,8), dtype='int')
        sign_table  = np.zeros((8,8), dtype='int')
        for a in range(0,8):
            for b in range(0,8):
                (color, sign) = self.ComputeColorSign(a, b)
                color_table[a,b] = color
                sign_table[a,b] = sign
        return (color_table, sign_table)

    def GetColorSign(self, formula_a, formula_b):
        '''Get the color and sign of the resulting potion from a binary formula 
        mixture.  Retrieved from lookup table (fast).
        '''
        color = self.color_table[formula_a,formula_b]
        sign = self.sign_table[formula_a,formula_b]
        return (color, sign)

    def RequireFromMixture(self, label_a, label_b, potion_set):
        ''' Keep only candidate solutions for which the mixture A,B results in 
        a potion (color, sign) flagged true in potion_set[color, sign].
        '''
        index = 0
        for x in permutations(range(0,8)):
            if self.mask[index]:
                formula_a = x[label_a]
                formula_b = x[label_b]
                (color, sign) = self.GetColorSign(formula_a, formula_b)
                self.mask[index] = potion_set[color,sign]
            index = index+1

    def RequireFromIngredient(self, label_a, potion_set):
        ''' Keep only candidate solutions for which a mixture with A results in 
        a potion (color, sign) flagged true in potion_set[color, sign].
        '''
        index = 0
        list_formula_b = range(0,8)
        list_formula_b.remove(label_a)
        for x in permutations(range(0,8)):
            if self.mask[index]:
                formula_a = x[label_a]
                feasible = False
                for formula_b in list_formula_b:
                    (color, sign) = self.GetColorSign(formula_a, formula_b)
                    if potion_set[color,sign]:
                        feasible = True
                        break
                self.mask[index] = feasible
            index = index+1



    def MixLabels(self,label_a,label_b):
        '''Return all possible results of mixing labels (A,B) as bool array indexed by [color,sign].
        '''
        potions = np.zeros((4,2),dtype='bool')
        index = 0
        for x in permutations(range(0,8)):
            if(self.mask[index]):
                formula_a = x[label_a]
                formula_b = x[label_b]
                (color, sign) = self.GetColorSign(formula_a,formula_b)
                potions[color][sign] = True
            index=index+1
        return potions

    def NumberSolutions(self):
        return np.sum(self.mask)

    def MatchTable(self):
        '''Return boolean table match[ingredient, formula] true if formula remains a candidate for the ingredient.
        '''
        match = np.zeros((8,8),dtype='bool')
        index = 0
        for x in permutations(range(0,8)):
            if self.mask[index]:
                for k in range(8):
                    match[k,x[k]] = True
            index = index+1
        return match