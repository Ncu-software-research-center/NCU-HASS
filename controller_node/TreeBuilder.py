import logging
import ConfigParser
import TreeDictionary
from BinaryTreeNode import BinaryTreeNode

class TreeBuilder(object):
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('/etc/hass.conf')

    def build_tree(self, needed_layers_string):
		tree_structure = TreeDictionary.TREE_DICTIONARY[needed_layers_string] #tree_dictionary[needed_layer_string]
		if len(tree_structure) == 0:
			return None
		binary_tree = BinaryTreeNode(tree_structure[0])
		for index in range(1, len(tree_structure)):
			binary_tree.insert(tree_structure[index])
		return binary_tree

if __name__ == "__main__":
	x = TreeBuilder()
	a = x.build_tree('111')
	print a.print_tree()