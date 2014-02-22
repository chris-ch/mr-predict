#
# -*- coding: utf-8 -*-
#
import json

from . import DecisionTreeFactory
from training import TrainingSet

class RandomForest(object):
    """Random Forest built from bagging regression trees."""
   
    def set_training_data(self, table, target, inclusion_ratio=.75,
                 exclude=[], min_count=5, min_gain=None,
                 split_sampling=42,
                 dimension_significance_threshold=0.5
                 ):
        """
        Prepares forest for the training phase.

        @param table: complete training set
        @param target: attribute to learn
        @param attr_frac: fraction of attributes to use for splitting
        @param exclude: list of attributes to exclude from learning
        @param min_count: threshold for leaf size
        @param min_gain: minimum gain in variance for splitting
        @param split_sampling: number of values to sample when considering a new split on an attribute

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
            
    def use_trees(self, trees):
        self.trees = trees
    
    def json(self):
        return json.dumps([tree.json() for tree in self.trees], cls=TreeJSONEncoder)
        
    def serialize(self, output):
        import cPickle
        cPickle.dump([tree for tree in self.trees], output)

    def predict(self, sample):
        """
        Predicts the regressand for a new sample
        """
        predictions = list()
        for tree in self.trees:
            prediction = tree.predict(sample)
            if prediction is not None:
                predictions.append(prediction)
        
        if len(predictions) == 0:
            return None
            
        return float(sum(predictions)) / len(predictions)

    def __str__(self):
        import os
        s = ''
        for root in self.trees:
            s += os.linesep + as_string(self.target, self.table, root) + os.linesep
            
        return s
        
class TreeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (LeafDecisionNode,)):
            return { 'value': obj.leaf_value }
            
        elif isinstance(obj, (DecisionNode,)):
            output = {
                'split_dimension': obj.split_dimension,
                'split_value': obj.split_value,
                'left_node': obj.left_node,
                'right_node': obj.right_node,
            }
            return output
            
        return json.JSONEncoder.default(self, obj)
        
        
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

