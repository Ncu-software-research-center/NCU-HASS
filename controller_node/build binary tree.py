#########################################################
#Copyright (c) 2020-present, drliang219
#All rights reserved.
#
#This source code is licensed under the BSD-style license found in the
#LICENSE file in the root directory of this source tree. 
##########################################################

import sys

# The following explains how to use this code:
# Suppose the system we want to detect has seven layers, where the highest layer is layer 6 (for example, the VM netwrok layer), and the lowest layer is layer 0 (for example, the host power layer).
# First, you should fill in the 'time_list' with the detection time of the detectors from layer 0 to layer 5 in order. For example, time_list = [0.06,0.81,3.45,0.53,1.1,1], the unit used in this example is seconds.
# Second, you should fill in the 'probability' list with the fault probability of the layers from layer 0 to layer 6. For example, probability = [0.172, 0.026, 0.161, 0.161, 0.161, 0.161, 0.161].
# Finally, you can execute this code to get the binary tree. The format of output is [[left subtree], root, [right subtree]]. If there is no left subtree or right subtree, the output may look like: [root, [right subtree]] or [[left subtree], root].
# For example, if the output is [0, [[[1], 2], 3, [[4], 5]]], the binary tree is as follows:
#          0
#           \
#            3
#           /  \
#          2    5
#         /    / 
#        1    4   
#
# reference: Yen-Lin Lee, Deron Liang, and Wei-Jen Wang. "Optimal Online Liveness Fault Detection for Multilayer Cloud Computing Systems." IEEE Transactions on Dependable and Secure Computing (2021).

time_list = [0.06,0.81,3.45,0.53,1.1,1]
probability = [0.172, 0.026, 0.161, 0.161, 0.161, 0.161, 0.161]
test_list = time_list


def insert_time_and_tree_list(lists):
  times = [ [None] * len(lists) for i in range(len(lists)) ]
  trees = [ [None] * len(lists) for i in range(len(lists)) ]
  for i in range(len(lists)):
    times[i][i]=lists[i]
    trees[i][i]=[i]
  return times, trees
  
def calculate_probability(begin, index, end):
  temp_left_probability = 0
  temp_right_probability = 0
  for index in range(begin, index+1):
    temp_left_probability += probability[index]
  for index in range(index+1, end+1):
    temp_right_probability += probability[index]
  temp_probability = temp_left_probability + temp_right_probability
  return temp_left_probability/temp_probability, temp_right_probability/temp_probability
"""
def build_tree(begin, end):
  #print("begin: "+str(begin)+";end: "+str(end))
  if begin > end  or end < 0:
    return 0, None
  else:
    tree_time = time_list[begin][end]
    #print("time:"+str(tree_time))
    tree = tree_list[begin][end]
  if tree_time ==None:
    tree = []
    tree_time = sys.maxsize
    for index in range(begin, end+1):
      temp_left_subtree_time, temp_left_subtree = build_tree(begin, index-1)
      #print("left: "+str(temp_left_subtree_time)+"; "+str(temp_left_subtree))
      temp_right_subtree_time, temp_right_subtree = build_tree(index+1, end)
      #print("right: "+str(temp_right_subtree_time)+"; "+str(temp_right_subtree))
      left_subtree_probability, right_subtree_probability = calculate_probability(begin, index, end+1)
      #print left_subtree_probability+ right_subtree_probability
      temp_time = time_list[index][index] + left_subtree_probability*float(temp_left_subtree_time) + right_subtree_probability*float(temp_right_subtree_time)
      if temp_time < tree_time:
        tree_time = temp_time
        temp_tree = []
        #print(str(temp_left_subtree)+" + "+str(index)+" + "+str(temp_right_subtree))
        if temp_left_subtree != None:
          temp_tree.append(temp_left_subtree)
        temp_tree.append(index)
        if temp_right_subtree != None:
          temp_tree.append(temp_right_subtree)
        tree = temp_tree
    time_list[begin][end] = tree_time
    tree_list[begin][end] = tree
  return tree_time, tree
"""
def dp_build_tree():
	# size of tree: 2 to N-1
	for size in range(2, len(test_list)+1):
		# starting point of tree
		for index in range(0, len(test_list)-size+1):
			# start filling out the list
			time, op_tree = select_optimal_tree(index, index+size-1)
			time_list[index][index+size-1] = time
			tree_list[index][index+size-1] = op_tree
			
def select_optimal_tree(begin, end):
	min_time = sys.maxsize
	for root in range(begin, end+1):
		# if no left subtree
		if root == begin:
			ltree_time = 0
		else:
			ltree_time = time_list[begin][root-1]
		# if no right subtree
		if root == end:
			rtree_time = 0
		else:
			rtree_time = time_list[root+1][end]
		ltree_p, rtree_p = calculate_probability(begin, root, end+1)
		time = time_list[root][root] + ltree_p*ltree_time + rtree_p*rtree_time
		if time < min_time:
			op_tree = []
			min_time = time
			if root != begin:
				ltree = tree_list[begin][root-1]
				op_tree.append(ltree)
			op_tree.append(root)
			if root != end:
				rtree = tree_list[root+1][end]
				op_tree.append(rtree)
	return min_time, op_tree
	
time_list, tree_list = insert_time_and_tree_list(test_list)
#print(time_list)
#, final_tree = build_tree(0, len(time_list)-1)
#print(time_list)
#print(tree_list)
#print(final_tree_time)
#print(final_tree)

dp_build_tree()
#print(time_list)
print(tree_list[0][len(time_list)-1])
