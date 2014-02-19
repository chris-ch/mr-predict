#
# -*- coding: utf-8 -*-
#
from . import DecisionTreeFactory
from training import TrainingSet

class RandomForest(object):
    """Random Forest built from bagging regression trees."""

    def __init__(self, table, target, inclusion_ratio=.75,
                 exclude=[], min_count=5, min_gain=None,
                 split_sampling=42,
                 dimension_significance_threshold=0.5
                 ):
        """Builds a new decision tree

        table -- complete training set
        target -- attribute to learn
        attr_frac -- fraction of attributes to use for splitting
        exclude -- list of attributes to exclude from learning
        min_count -- threshold for leaf size
        min_gain -- minimum gain in variance for splitting
        split_sampling -- number of values to sample when considering
                          a new split on an attribute

        """
        self.table = table
        self.target = target
        self.inclusion_ratio = inclusion_ratio
        self.exclude = exclude
        self.min_count = min_count
        self.min_gain = min_gain
        self.split_sampling = split_sampling
        self.dimension_significance_threshold = dimension_significance_threshold

        self.target = target
        self.trees = []

    def grow_trees(self, trees_count):
        """Grow a given number of trees."""
        factory = DecisionTreeFactory(self.table, self.target,
                              self.inclusion_ratio,
                              self.exclude,
                              self.min_count,
                              self.min_gain,
                              self.split_sampling,
                              self.dimension_significance_threshold
                              )
        for i in range(trees_count):
            tree = factory.create()
            self.trees.append(tree)

    def predict(self, inst):
        """Predict the regressand for a new instance."""
        s = sum([tree.predict(inst) for tree in self.trees])
        return float(s) / len(self.trees)

    def __str__(self):
        import os
        s = ''
        for root in self.trees:
            s += os.linesep + as_string(self.target, self.table, root) + os.linesep
            
        return s
        
        
def as_string(target, table, node, depth=0):
    s = '  | ' * depth
    if node.is_leaf():
        s += '%.2f [count=%d, Var=%.1e]\n' % (
                node.leaf_value, table.count(), table.variance(target))
    else:
        s += '%s(%.2f) [count=%d, Var=%.1e]\n' % (
                node.split.dimension, node.split.val, table.count(), table.variance(target))
        
        s += "%s%s" % (
            as_string(target, node.split.left_table, node.left_node, depth + 1), 
            as_string(target, node.split.right_table, node.right_node, depth + 1),
            )
        
    return s

