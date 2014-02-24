#
# -*- coding: utf-8 -*-
#

import logging
from predict.decisiontree import DecisionTreeFactory
from predict.decisiontree import LeafDecisionNode
from predict.decisiontree import DecisionNode
from training import TrainingSet

_LOG = logging.getLogger('training')

def serialize_forests(forests, output):
    import cPickle
    trees = list()
    for forest in forests:
        trees += forest.trees
        
    cPickle.dump(trees, output)

class RandomForest(object):
    """Random Forest built from bagging regression trees."""

    def __init__(self):
        self.trees = []

    def set_training_data(self, table, target, inclusion_ratio=.75,
                 exclude=[], min_count=None, min_gain=None,
                 split_sampling=50,
                 dimension_significance_threshold=0.5
                 ):
        """
        Prepares forest for the training phase.

        @param table: complete training set
        @param target: attribute to learn
        @param inclusion_ratio: fraction of dimensions to use for splitting
        @param exclude: list of attributes to exclude from learning
        @param min_count: threshold for leaf size
        @param min_gain: minimum gain in variance for splitting
        @param split_sampling: number of values to sample when considering a new split on an attribute

        """
        assert target in table.get_dimensions(), 'target column "%s" is missing in input dataset' % target
        _LOG.debug('building forest using new training data')
        self.table = table
        table_size = table.count()
        _LOG.debug('training data size: %d' % table_size)
        self.target = target
        self.inclusion_ratio = inclusion_ratio
        self.exclude = exclude
        if min_count is None:
            min_count = max(round(0.05 * table_size), 1)
            
        self.min_count = min_count
        _LOG.debug('min leaf size set to %d' % self.min_count)
        self.min_gain = min_gain
        self.split_sampling = split_sampling
        self.dimension_significance_threshold = dimension_significance_threshold
        self.target = target
        self._tree_factory = None

    @property
    def tree_factory(self):
        if self._tree_factory is None:
            self._tree_factory = DecisionTreeFactory(self.table, self.target,
                self.inclusion_ratio,
                self.exclude,
                self.min_count,
                self.min_gain,
                self.split_sampling,
                self.dimension_significance_threshold
                )
        
        return self._tree_factory

    def grow_tree(self):
        """Grow a single tree."""
        _LOG.debug('growing a new tree')
        tree = self.tree_factory.create()
        self.trees.append(tree)
        return tree
            
    def grow_trees(self, trees_count):
        """Grow a given number of trees."""
        for i in range(trees_count):
            tree = self.grow_tree()

    def use_trees(self, trees):
        self.trees += trees

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

