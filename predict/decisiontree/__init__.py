#
# -*- coding: utf-8 -*-
#
import logging
import random
import os
import abc

_LOG = logging.getLogger('training')

class DecisionTreeFactory(object):
    
    def __init__(self, table, target, inclusion_ratio,
                 exclude, min_items_count, min_split_gain,
                 samples_split_size, dimension_significance_threshold):
        """
        @param table: full training table
        @param target: dimension to learn
        @param inclusion_ratio: fraction of dimensions to use for splitting
        @param exclude: list of dimensions to exclude from learning
        @param min_items_count: threshold for leaf size
        @param min_split_gain: minimum gain when splitting
        @param samples_split_size: number of values to sample when considering a new split on a dimension
        @param dimension_significance_threshold: ratio of non-null values considered as significant in a given dimension
        """
        assert table.check_column(target), 'target column "%s" is missing in input dataset' % target
        self.table = table
        self.exclude = exclude
        self.target = target
        min_items_count = max(2, min_items_count) # no need to go below 2
        self.min_items_count = min_items_count
        _LOG.info('no split on groups below %d samples' % self.min_items_count)
        self.min_split_gain = min_split_gain
        self.samples_split_size = samples_split_size
        self.dimensions = [dim for dim in self.table.get_dimensions()
                      if dim != self.target and dim not in self.exclude]
        self.dimensions_split_size = max(int(inclusion_ratio * len(self.dimensions)), 1)
        _LOG.info('the algorithm will be testing %d dimensions at each node for the best split' % self.dimensions_split_size)
        self.dimension_significance_threshold = dimension_significance_threshold

    def create(self):
        root = self._load_node(self.table)
        return root

    def _load_node(self, table):
        """
        @param table: training subset at the node level
        """
        if table.count() < self.min_items_count:
            leaf_value = table.target_median()
            _LOG.info('low limit reached (%d), creating new leaf node for value %s' % (table.count(), leaf_value))
            node = LeafDecisionNode(leaf_value)
            
        elif table.target_entropy() == 0.:
            leaf_value = table.target_median()
            _LOG.info('output identical for all %d elements, creating new leaf node for value %s' % (table.count(), leaf_value))
            node = LeafDecisionNode(leaf_value)
        
        else:
            _LOG.info('splitting %d elements' % table.count())
            best_split, best_dimension, best_value = self._select_split(self.dimensions, table)
            if best_split is None:
                _LOG.debug('-------B1')
                leaf_value = table.target_median()
                _LOG.info('no convenient split found, creating new leaf node for %d elements for value %s' % (table.count(), leaf_value))
                node = LeafDecisionNode(leaf_value)
            else:
                _LOG.debug('-------B2')
                node_entropy = table.target_entropy()
                gain = 1. - best_split['score'] / node_entropy
                _LOG.info('entropy at current node is %.4f' % (node_entropy))
                _LOG.info('assessing split %d / %d (score %.4f) creating a gain in entropy of %.1f%%' % (best_split['left_table'].count(), best_split['right_table'].count(), best_split['score'], 100.0 * gain))
                if gain <= self.min_split_gain:
                    _LOG.debug('-------C1')
                    leaf_value = table.target_median()
                    _LOG.info('gain too low, creating new leaf node for %d elements for value %s' % (table.count(), leaf_value))
                    node = LeafDecisionNode(leaf_value)
                    
                else:
                    _LOG.debug('-------C2')
                    _LOG.info('assessment succesful: creating split')
                    _LOG.info('creating left subnode for %d elements' % (best_split['left_table'].count()))
                    left_node = self._load_node(best_split['left_table'])
                    _LOG.info('creating right subnode for %d elements' % (best_split['right_table'].count()))
                    right_node = self._load_node(best_split['right_table'])
                    node = DecisionNode(split_value=best_value,
                            split_dimension=best_dimension,
                            left_node=left_node,
                            right_node=right_node
                            )

        return node

    def _select_split(self, tree_dimensions, table):
        """ Restricting the dimensions prevents cross-correlation in Random Forests """
        dimensions = random.sample(tree_dimensions, self.dimensions_split_size)
        best_split = None
        best_dimension = None
        best_value = None
        for dimension in dimensions:
            _LOG.debug('testing split value on dimension %s for max %d samples' % (dimension, self.samples_split_size))
            for split_value in table.sample_measures(dimension, self.samples_split_size):
                if split_value is None:
                    continue
                    
                _LOG.debug('testing split value %s' % split_value)
                split = self._create_split(dimension, split_value, table)
                _LOG.debug('resulting split %s' % split)
                if not best_split or split['score'] < best_split['score']:
                    best_split = split
                    best_dimension = dimension
                    best_value = split_value
                    
        _LOG.debug('keeping best split "%s" (%s)' % (best_dimension, best_value))
        return (best_split, best_dimension, best_value)
    
    def _create_split(self, dimension, split_value, table):
        """
        Splits the provided table along dimension based on split_value.
        """
        left_table, right_table, null_table = table.split(dimension, split_value)
        null_table.random_split(left_table, right_table)
        
        if left_table.count() == 0 or right_table.count() == 0:
            score = table.target_entropy() # score left unchanged
            
        else:
            alpha = float(left_table.count()) / table.count()
            left_entropy = left_table.target_entropy()
            right_entropy = right_table.target_entropy()
            # we try to minimize global entropy
            # so even if one of the 2 sets has a higher entropy
            # the split is still acceptable if the corresponding
            # number of elements is lower than in the other set
            score = alpha * left_entropy + (1.0 - alpha) * right_entropy
        
        split = {
            'score': score,
            'left_table': left_table,
            'right_table': right_table
        }
        return split

class BaseDecisionNode(object):
    __metaclass__ = abc.ABCMeta
    
    @abc.abstractmethod
    def is_leaf(self):
        """ Marker for leaves"""
        return self.left_node == None or self.right_node == None
    
    def predict(self, sample):
        """Predicts the regressand value for sample"""
        if self.is_leaf():
            _LOG.debug('predicting: %s' % self.leaf_value)
            return self.leaf_value
        
        else:
            if sample.has_key(self.split_dimension):
                if sample[self.split_dimension] <= self.split_value:
                    return self.left_node.predict(sample)
                    
                else:
                    return self.right_node.predict(sample)
            
            else:
                left_node_value = self.left_node.predict(sample) 
                right_node_value = self.right_node.predict(sample)
                return 0.5 * (left_node_value + right_node_value) 
         
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
        
