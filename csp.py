"""CSP (Constraint Satisfaction Problems) problems and solvers. (Chapter 6)."""
"""Adapted from https://github.com/aimacode/aima-python"""

from utils import argmin_random_tie, count, first
import search

from collections import defaultdict
from functools import reduce

import itertools
import re
import random
import graph_drawing as gui
import sys, getopt
import time

retardo = 1

class CSP(search.Problem):
	"""This class describes finite-domain Constraint Satisfaction Problems.
	A CSP is specified by the following inputs:
		variables   A list of variables; each is atomic (e.g. int or string).
		domains     A dict of {var:[possible_value, ...]} entries.
		neighbors   A dict of {var:[var,...]} that for each variable lists
					the other variables that participate in constraints.
		constraints A function f(A, a, B, b) that returns true if neighbors
					A, B satisfy the constraint when they have values A=a, B=b


	The following are just for debugging purposes:
		display(a)              Print a human-readable representation
	"""

	def __init__(self, variables, domains, neighbors, constraints):
		"""Construct a CSP problem. If variables is empty, it becomes domains.keys()."""
		variables = variables or list(domains.keys())

		self.variables = variables
		self.domains = domains
		self.neighbors = neighbors
		self.constraints = constraints
		self.initial = ()
		self.curr_domains = None
		self.nassigns = 0


	def assign(self, var, val, assignment):
		"""Add {var: val} to assignment; Discard the old value if any."""
		assignment[var] = val
		self.nassigns += 1

	def unassign(self, var, assignment):
		"""Remove {var: val} from assignment.
		DO NOT call this if you are changing a variable to a new value;
		just call assign for that."""
		if var in assignment:
			del assignment[var]

	def nconflicts(self, var, val, assignment):
		"""Return the number of conflicts var=val has with other variables."""
		# Subclasses may implement this more efficiently
		def conflict(var2):
			return (var2 in assignment and
					not self.constraints(var, val, var2, assignment[var2]))
		return count(conflict(v) for v in self.neighbors[var])

	def display(self, assignment):
		"""Show a human-readable representation of the CSP."""
		# Subclasses can print in a prettier way, or display with a GUI
		print('CSP with assignment:', assignment)


	def actions2(self, var, assignment):
		domain = []
		if var in assignment:
			domain.append(assignment[var])
		else:
			domain = [val for val in self.domains[var]
					if self.nconflicts(var, val, assignment) == 0]
		return domain


	def goal_test(self, state):
		"""The goal is to assign all variables, with all constraints satisfied."""
		assignment = dict(state)
		return (len(assignment) == len(self.variables)
				and all(self.nconflicts(variables, assignment[variables], assignment) == 0
						for variables in self.variables))

	# These are for constraint propagation

	def support_pruning(self):
		"""Make sure we can prune values from domains. (We want to pay
		for this only if we use it.)"""
		if self.curr_domains is None:
			self.curr_domains = {v: list(self.domains[v]) for v in self.variables}

	def suppose(self, var, value):
		"""Start accumulating inferences from assuming var=value."""
		self.support_pruning()
		removals = [(var, a) for a in self.curr_domains[var] if a != value]
		for i in self.domains:  #revisa en todos los dominios
			if i != var:        #se salta la variable en la que el dominio ya se reviso
				if value in self.domains[i]:
					removals.append((i,value))
		self.curr_domains[var] = [value]
		return removals

	def prune(self, var, value, removals):
		"""Rule out var=value."""
		self.curr_domains[var].remove(value)
		if removals is not None:
			removals.append((var, value))

	def choices(self, var):
		"""Return all values for var that aren't currently ruled out."""
		return (self.curr_domains or self.domains)[var]

	def restore(self, removals):
		"""Undo a supposition and all inferences from it."""
		for B, b in removals:
			self.curr_domains[B].append(b)

# ______________________________________________________________________________
#                       Constraint Propagation with AC-3
# ______________________________________________________________________________
def AC3(csp, queue=None, removals=None):
	"""[Figure 6.3]"""
	if queue is None:
		queue = [(Xi, Xk) for Xi in csp.variables for Xk in csp.neighbors[Xi]]
	csp.support_pruning()
	while queue:
		(Xi, Xj) = queue.pop()
		#print(csp.curr_domains[Xi])
		if revise(csp, Xi, Xj, removals):
			if not csp.curr_domains[Xi]:
				return False
			for Xk in csp.neighbors[Xi]:
				if Xk != Xj:
					queue.append((Xk, Xi))
	return True

def revise(csp, Xi, Xj, removals):
	"""Return true if we remove a value."""
	revised = False
	for x in csp.curr_domains[Xi][:]:
		# If Xi=x conflicts with Xj=y for every possible y, eliminate Xi=x
		if all(not csp.constraints(Xi, x, Xj, y) for y in csp.curr_domains[Xj]):
			csp.prune(Xi, x, removals)
			revised = True
	#eliminar en las demas variables el dominio
	return revised

# ______________________________________________________________________________
#                       CSP Backtracking Search
#                           Variable ordering
# ______________________________________________________________________________

def first_unassigned_variable(assignment, csp):
	"""The default variable order."""
	return first([var for var in csp.variables if var not in assignment])

def mrv(assignment, csp):
	"""Minimum-remaining-values heuristic."""
	return argmin_random_tie(
		[v for v in csp.variables if v not in assignment],
		key=lambda var: num_legal_values(csp, var, assignment))

def num_legal_values(csp, var, assignment):
	if csp.curr_domains:
		return len(csp.curr_domains[var])
	else:
		return count(csp.nconflicts(var, val, assignment) == 0
					 for val in csp.domains[var])

# ______________________________________________________________________________
#                           Value ordering
# ______________________________________________________________________________

def unordered_domain_values(var, assignment, csp):
	"""The default value order."""
	return csp.choices(var)

def lcv(var, assignment, csp):
	"""Least-constraining-values heuristic."""
	return sorted(csp.choices(var),
				  key=lambda val: csp.nconflicts(var, val, assignment))

# ______________________________________________________________________________
#                               Inference
# ______________________________________________________________________________

def no_inference(csp, var, value, assignment, removals):
	return True

def mac(csp, var, value, assignment, removals):
	"""Maintain arc consistency."""
	inference = AC3(csp, [(X, var) for X in csp.neighbors[var]], removals)
	update_domain(csp, assignment)
	return inference

# ______________________________________________________________________________
#						The search, proper
# ______________________________________________________________________________

def backtracking_search(csp,select_unassigned_variable=first_unassigned_variable,order_domain_values=unordered_domain_values,inference=no_inference):
	def backtrack(assignment):
		if len(assignment) == len(csp.variables):
			return assignment
		var = select_unassigned_variable(assignment, csp)

		for value in order_domain_values(var, assignment, csp):
			if 0 == csp.nconflicts(var, value, assignment):
				csp.assign(var, value, assignment)
				gui.circle_assigment(var,value,True)
				removals = csp.suppose(var, value)
				update_domain(csp,assignment)
				if inference(csp, var, value, assignment, removals):
					#gui.wait()
					time.sleep(retardo)
					result = backtrack(assignment)
					if result is not None:
						return result
				csp.restore(removals)
		csp.unassign(var, assignment)
		gui.circle_unassigment(var)
		print("Des->" , var)
		#gui.wait()
		time.sleep(retardo)
		return None

	result = backtrack({})
	assert result is None or csp.goal_test(result)
	return result

def update_domain(csp, assignment):
	print('\n')
	csp.display(assignment)
	for Xi in csp.variables:
		domain = csp.curr_domains[Xi]
		#domain = csp.actions2(Xi,assignment)
		print(Xi, '->', domain)
		if Xi in assignment:
			gui.update_assign_domain(Xi,domain,True)
		else:
			gui.update_assign_domain(Xi, domain,False)

# ______________________________________________________________________________
#-------------------- CSP problem formulation ----------------
#					Return true if no constraint
# ______________________________________________________________________________

def Table_constraint(A, a, B, b):
	"""A constraint saying two neighboring must be compatible and diferent."""

	#values    a,b
	#variables A,B
	you   = ["M","J","E","T","A"]
	mike  = ["Y","E","T","A"]
	james = ["Y","M","E","A"]
	emily = ["Y","M","J"]
	tom   = ["Y","M","E","A"]
	amy   = ["Y","J","T"]

	result_1 = False
	result_2 = False

	if a == 'Y':
		if b in you:
			result_1 = True
	elif a == 'M':
		if b in mike:
			result_1 = True
	elif a == 'J':
		if b in james:
			result_1 = True
	elif a == 'E':
		if b in emily:
			result_1 = True
	elif a == 'T':
		if b in tom:
			result_1 = True
	elif a == 'A':
		if b in amy:
			result_1 = True

	if b == 'Y':
		if a in you:
			result_2 = True
	elif b == 'M':
		if a in mike:
			result_2 = True
	elif b == 'J':
		if a in james:
			result_2 = True
	elif b == 'E':
		if a in emily:
			result_2 = True
	elif b == 'T':
		if a in tom:
			result_2 = True
	elif b == 'A':
		if a in amy:
			result_2 = True

	if result_1 == True and result_2 == True:
		return True
	else:
		return False

variables = ("Farming","Design","Manufacturing","Packing","Transportation","President")

neighbors = {"Farming": 		["Design","Transportation"],
			 "Design": 			["Farming","Manufacturing"],
			 "Manufacturing": 	["Design","Packing"],
			 "Packing": 		["Manufacturing","Transportation"],
			 "Transportation": 	["Farming","Packing"],
			 "President": 		["Farming","Design","Manufacturing","Packing","Transportation"]}

domains = {"Farming"			: 'MJETA',
		   "Design" 			: 'MJETA',
		   "Manufacturing" 		: 'MJETA',
		   "Packing" 			: 'MJETA',
		   "Transportation"		: 'MJETA',
		   "President"			: 'YMJETA'}

network = CSP(variables, domains, neighbors, Table_constraint)

if __name__ == "__main__":
	gui.init_gui()
	for station in domains:
		for name in domains[station]:
			gui.circle_assigment(station,name,False)

	variableSelection = first_unassigned_variable
	orderValues = unordered_domain_values
	infer = no_inference

	infer=mac
	result = backtracking_search(network,select_unassigned_variable=variableSelection,order_domain_values=orderValues,inference=infer)

	f = open("outputCSP.log", "w")
	print('\n\nCSP with final assignment')
	f.write('CSP with final assignment\n\n')
	for station in result:
		name = result[station]
		if name == 'Y':
			name = 'You'
		elif name == 'M':
			name = 'Mike'
		elif name == 'J':
			name = 'James'
		elif name == 'E':
			name = 'Emily'
		elif name == 'T':
			name = 'Tom'
		elif name == 'A':
			name = 'Amy'
		print(station, '->',name)
		f.write('{0} in {1}\n'.format(station, name))
	gui.wait()
	f.close()
