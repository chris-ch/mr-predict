#
# -*- coding: utf-8 -*-
#
import logging
import random
import os
import abc

_LOG = logging.getLogger('training')

class DecisionTreeFactory(object):
    
    def __init__(self, training_set, target, inclusion_ratio,
                 exclude, min_items_count, min_split_gain,
                 samples_split_size, dimension_significance_threshold):
        """
        @param training_set: full training set
        @param target: dimension to learn
        @param inclusion_ratio: fraction of dimensions to use for splitting
        @param exclude: list of dimensions to exclude from learning
        @param min_items_count: threshold for leaf size
        @param min_split_gain: minimum gain when splitting
        @param samples_split_size: number of values to sample when considering a new split on a dimension
        @param dimension_significance_threshold: ratio of non-null values considered as significant in a given dimension
        """
        assert training_set.check_column(target), 'target column "%s" is missing in input dataset' % target
        self.training_set = training_set
        self.exclude = exclude
        self.target = target
        min_items_count = max(2, min_items_count) # no need to go below 2
        self.min_items_count = min_items_count
        _LOG.info('no split on groups below %d samples' % self.min_items_count)
        self.min_split_gain = min_split_gain
        self.samples_split_size = samples_split_size
        self.dimensions = [dim for dim in self.training_set.get_dimensions()
                      if dim != self.target and dim not in self.exclude]
        self.dimensions_split_size = max(int(inclusion_ratio * len(self.dimensions)), 1)
        _LOG.info('the algorithm will be testing %d dimensions at each node for the best split' % self.dimensions_split_size)
        self.dimension_significance_threshold = dimension_significance_threshold

    def create(self):
        root = self._create_node(self.training_set)
        return root

    def _create_node(self, training_set):
        """
        @param training_set: training subset at the node level
        """
        set_size = training_set.count()
        leaf_value = training_set.target_median()
        node_entropy = training_set.target_entropy()
        if set_size < self.min_items_count:
            _LOG.info('low limit reached (%d), creating new leaf node for value %s' % (set_size, leaf_value))
            node = LeafDecisionNode(leaf_value)
            
        elif node_entropy == 0.:
            _LOG.info('output identical for all %d elements, creating new leaf node for value %s' % (set_size, leaf_value))
            node = LeafDecisionNode(leaf_value)
        
        else:
            _LOG.info('splitting %d elements' % set_size)
            best_split, best_dimension, best_value = select_split(self.dimensions,
                training_set,
                self.dimensions_split_size,
                self.samples_split_size
                )
            if best_split is None:
                _LOG.info('no convenient split found, creating new leaf node for %d elements for value %s' % (set_size, leaf_value))
                node = LeafDecisionNode(leaf_value)
            else:
                gain = 1. - best_split['score'] / node_entropy
                _LOG.info('entropy at current node is %.4f' % (node_entropy))
                _LOG.info('assessing split %d / %d (score %.4f) creating a gain in entropy of %.1f%%' % (best_split['left_ts'].count(), best_split['right_ts'].count(), best_split['score'], 100.0 * gain))
                if gain <= self.min_split_gain:
                    _LOG.info('gain too low, creating new leaf node for %d elements for value %s' % (set_size, leaf_value))
                    node = LeafDecisionNode(leaf_value)
                    
                else:
                    _LOG.info('assessment succesful: creating split')
                    _LOG.info('creating left subnode for %d elements' % (best_split['left_ts'].count()))
                    left_node = self._create_node(best_split['left_ts'])
                    _LOG.info('creating right subnode for %d elements' % (best_split['right_ts'].count()))
                    right_node = self._create_node(best_split['right_ts'])
                    node = DecisionNode(split_value=best_value,
                            split_dimension=best_dimension,
                            left_node=left_node,
                            right_node=right_node
                            )

        return node
    
def select_split(tree_dimensions, training_set, dimensions_split_size, samples_split_size):
    """ Restricting the dimensions prevents cross-correlation in Random Forests """
    dimensions = random.sample(tree_dimensions, dimensions_split_size)
    best_split = None
    best_dimension = None
    best_value = None
    for dimension in dimensions:
        (dim_split, dim_value) = assess_split(training_set, dimension, samples_split_size)
        if dim_split and (not best_split or dim_split['score'] < best_split['score']):
            best_split = dim_split
            best_value = dim_value
            best_dimension = dimension
        
    _LOG.debug('keeping best split "%s" (%s)' % (best_dimension, best_value))
    return (best_split, best_dimension, best_value)

def assess_split(training_set, dimension, size):
    """
    Assessing the effect of N random splits along dimension.
    """
    _LOG.debug('testing split value on dimension %s for %d samples' % (dimension, size))
    best_split = None
    best_value = None
    candidate_values = training_set.sample_measures(dimension, size)
    for split_value in candidate_values:
        if split_value is None:
            continue
            
        _LOG.debug('testing split value %s' % split_value)
        split = create_split(training_set, dimension, split_value)
        _LOG.debug('resulting split %s' % split)
        if not best_split or split['score'] < best_split['score']:
            best_split = split
            best_value = split_value
            
    return best_split, best_value
    
def create_split(training_set, dimension, split_value):
    """
    Splits the provided set along dimension based on split_value.
    """
    left_ts, right_ts, null_ts = training_set.split(dimension, split_value)
    null_ts.random_split(left_ts, right_ts)
    
    if left_ts.count() == 0 or right_ts.count() == 0:
        score = training_set.target_entropy() # score left unchanged
        
    else:
        alpha = float(left_ts.count()) / training_set.count()
        left_entropy = left_ts.target_entropy()
        right_entropy = right_ts.target_entropy()
        # we try to minimize global entropy
        # so even if one of the 2 sets has a higher entropy
        # the split is still acceptable if the corresponding
        # number of elements is lower than in the other set
        score = alpha * left_entropy + (1.0 - alpha) * right_entropy
    
    split = {
        'score': score,
        'left_ts': left_ts,
        'right_ts': right_ts
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
        
