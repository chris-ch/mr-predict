#
# -*- coding: utf-8 -*-
#
import logging
import random
import os
import abc
import json

_LOG = logging.getLogger('regression')

class DecisionTreeFactory(object):
    
    def __init__(self, table, target, inclusion_ratio,
                 exclude, min_items_count, min_variance_gain,
                 samples_split_size, dimension_significance_threshold):
        """
        @param table: full training table
        @param target: dimension to learn
        @param inclusion_ratio: fraction of dimensions to use for splitting
        @param exclude: list of dimensions to exclude from learning
        @param min_items_count: threshold for leaf size
        @param min_variance_gain: minimum gain in variance for splitting
        @param samples_split_size: number of values to sample when considering a new split on a dimension
        @param dimension_significance_threshold: ratio of non-null values considered as significant in a given dimension
        """
        self.table = table
        self.exclude = exclude
        self.target = target
        self.min_items_count = min_items_count
        self.min_variance_gain = min_variance_gain
        self.samples_split_size = samples_split_size
        self.dimensions = [attr for attr in self.table.get_dimensions()
                      if attr != self.target and attr not in self.exclude]
        self.dimensions_split_size = min(int(inclusion_ratio * len(self.dimensions)), 1)
        self.dimension_significance_threshold = dimension_significance_threshold

    def create(self):
        root = self._load_node(self.table)
        return root

    def _load_node(self, table):
        """
        @param table: training subset at the node level
        """
        if table.count() < self.min_items_count or table.variance(self.target) == 0.:
            leaf_value = table.mean(self.target)
            node = LeafDecisionNode(leaf_value)
        
        else:
            significant_dimensions = self._keep_significant_dimensions(self.dimensions, table)
            if len(significant_dimensions) == 0:
                leaf_value = table.mean(self.target)
                node = LeafDecisionNode(leaf_value)
            else:    
                best_split, best_dimension, best_value = self._select_split(significant_dimensions, table)
                gain = 1. - best_split.exp_var / table.variance(self.target)
                if gain <= self.min_variance_gain:
                    leaf_value = table.mean(self.target)
                    node = LeafDecisionNode(leaf_value)
                    
                else:
                    left_node = self._load_node(best_split.left_table)
                    right_node = self._load_node(best_split.right_table)
                    node = DecisionNode(split_value=best_value,
                            split_dimension=best_dimension,
                            left_node=left_node,
                            right_node=right_node
                            )

        return node

    def _keep_significant_dimensions(self, dimensions, table):
        significant_dimensions = []
        for dimension in dimensions:
            # checks size of sample for which measure is known
            significance_ratio = float(table.count_not_null(dimension)) / float(table.count())
            if  significance_ratio >= self.dimension_significance_threshold:
                significant_dimensions.append(dimension)
        
        return significant_dimensions

    def _select_split(self, tree_dimensions, table):
        """ Restricting the dimensions prevents cross-correlation in Random Forests """
        dimensions = random.sample(tree_dimensions, self.dimensions_split_size)
        best_split = None
        best_dimension = None
        best_value = None
        for dimension in dimensions:
            for split_value in table.sample_measures(dimension, self.samples_split_size):
                split = self._create_split(dimension, split_value, table)
                if not best_split or split.exp_var < best_split.exp_var:
                    best_split = split
                    best_dimension = dimension
                    best_value = split_value
                    
        return (best_split, best_dimension, best_value)
    
    def _create_split(self, dimension, split_value, table):
        """
        Splits the provided table along dimension based on split_value.
        """
        left_table, right_table, null_table = table.split(dimension, split_value)
        if null_table.count() > 0:
            half_index = int(0.5 * len(null_table))
            left_table += null_table[:half_index]
            right_table += null_table[half_index:]
        
        if left_table.count() == 0 or right_table.count() == 0:
            exp_var = table.variance(self.target)
            
        else:
            k = float(left_table.count()) / table.count()
            left_var = left_table.variance(self.target)
            right_var = right_table.variance(self.target)
            exp_var = k * left_var + (1.0 - k) * right_var
        
        split = DimensionSplit(exp_var, left_table, right_table, null_table)
        return split

class DimensionSplit(object):
    """ Records parameters for a dimension split """

    def __init__(self, exp_var, left_table, right_table, null_table):
        self.exp_var = exp_var
        self.left_table = left_table
        self.right_table = right_table
        self.null_table = null_table

class BaseDecisionNode(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def is_leaf(self):
        """ Marker for leaves"""
        return
        return self.left_node == None or self.right_node == None
    
    def predict(self, sample):
        """Predicts the regressand value for sample"""
        if self.is_leaf():
            return self.leaf_value
        
        else:
            if sample.has_key(self.split_dimension):
                if sample[self.split_dimension] <= self.split_value:
                    return self.left_node.predict(sample)
                    
                else:
                    return None
            
            else:
                return self.right_node.predict(sample)
                    
class LeafDecisionNode(BaseDecisionNode):
    
    def __init__(self, leaf_value):
        """
        Creates a new leaf node for a decision tree
        """
        super(LeafDecisionNode, self).__init__()
        self.leaf_value = leaf_value
        
    def is_leaf(self):
        """ Marker for leaves"""
        return True
    
class DecisionNode(BaseDecisionNode):
    """
    The goal of the training phase is to build a tree of decision nodes,
    which makes instances of this class the only objects one would want to keep
    before starting the testing phase.
    """
    
    def __init__(self, split_value, split_dimension, left_node, right_node):
        """
        Creates a new node for a decision tree
        """
        super(DecisionNode, self).__init__()
        self.split_value = split_value
        self.split_dimension = split_dimension
        self.left_node = left_node
        self.right_node = right_node
        
    def is_leaf(self):
        """ Marker for leaves"""
        return False
        
        
