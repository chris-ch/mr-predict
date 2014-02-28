#
# -*- coding: utf-8 -*-
#
import logging
_LOG = logging.getLogger('training')

import random
from collections import defaultdict

from predict.decisiontree import tools

def as_float(s):
    try:
        v = float(s)
        return v
    except ValueError:
        return None
        
def as_int(s):
    try:
        v = int(s)
        return v
    except ValueError:
        return None
       
class TrainingSetFactory(object):

    def train_csv(self, input_file, target_name='target', output_sampling=5, ignore_columns=None):
        import csv
        _LOG.info('loading training set')
        if ignore_columns is None:
            ignore_columns = list()
            
        ts = TrainingSet()
        input_data = csv.reader(input_file, delimiter=',')
        first_row = next(input_data)[1:]
        header = [label for label in first_row if label not in ignore_columns]
        header_index = set([index for index, label in enumerate(first_row) if label not in ignore_columns])
         
        assert target_name in header, 'target column "%s" is missing in input dataset' % target_name
        target_index = first_row.index(target_name)
        ts.set_dimensions(header)
        output_categories = set()
        for columns in input_data:
            row = list()
            for index, cell in enumerate(columns[1:]):
                if index not in header_index: continue
                value = as_int(cell)
                if not value:
                    value = as_float(cell)
                
                if len(output_categories) < 3:
                    if index == target_index:
                        output_categories.add(value)
                    
                row.append(value)

            ts.insert(row)

        ts.end_insert(target_name, output_sampling, binary_output=len(output_categories) == 2)
        print 'output categories', output_categories
        _LOG.info('training set: %d samples and %d dimensions loaded' % (ts.count(), len(header)))
        return ts

    def train_x_y(self, func, count, range_x, range_y,
            target_name='target', missing_rate=0.0):
        """
        For double entry functions.

        @param func: function used a reference for training
        @param count: number of runs
        @param range_x: range for dimension x as a tuple (min, max)
        @param range_y: range for dimension y as a tuple (min, max)
        @param target_name: output dimension
        @param missing_rate: rate  which one of the inputs may be missing
        """
        loc_table = TrainingSet()
        keys = ['x', 'y']
        for index in xrange(count):
            log_data = {}
            dimension_to_skip = None
            missing_input = random.uniform(0.0, 1.0) <= missing_rate
            if missing_input:
                dimension_to_skip = random.choice(keys)

            x = random.uniform(*range_x)
            if dimension_to_skip != 'x':
                log_data['x'] = x

            y = random.uniform(*range_y)
            if dimension_to_skip != 'y':
                log_data['y'] = y

            log_data['target'] = func(x, y)
            loc_table.insert(log_data)

        return loc_table

class TrainingSet(object):

    """
        Interface to datastore
    """

    def __init__(self):
        self._dimensions = list()
        self._index = dict()
        self._items = list()
        # caching
        self._list_not_null = dict()
        self._entropies = dict()
        self._medians = dict()
        self._output_min = None
        self._output_max = None
        self._output_sampling = None

    def _get_list_not_null(self, dim):
        """
        Sorted list of non null values for a specific dimension.
        """
        if not self._list_not_null.has_key(dim):
            index = self._index[dim]
            not_null_items = [item[index] for item in self._items
                if item[index] is not None]                                    
            self._list_not_null[dim] = sorted(not_null_items)
            
        return self._list_not_null[dim]

    def _get_median(self, dim):
        """
        Computes the statistics (median, entropy) for a dimension
        """
        if not self._medians.has_key(dim):
            values = self._get_list_not_null(dim)
            if len(values) == 0:
                median = None

            else:
                median = tools.median(values)
                
            self._medians[dim] = median
            
        return self._medians[dim]

    def _get_entropy(self, dim):
        """
        Computes the statistics (median, entropy) for a dimension
        """
        if not self._entropies.has_key(dim):
            values = self._get_list_not_null(dim)
            if len(values) == 0:
                entropy = None

            else:
                entropy = tools.entropy(values, self._output_min, self._output_max, accuracy=self._output_sampling)
                
            self._entropies[dim] = entropy
            
        return self._entropies[dim]

    def _get_items(self):
        return self._items

    def _create_child_table(self):
        ts = TrainingSet()
        ts.set_dimensions(self.get_dimensions())
        ts._output_sampling = self._output_sampling
        ts._output_min = self._output_min
        ts._output_max = self._output_max
        self._binary_output = False
        return ts

    def set_dimensions(self, dimensions):
        self._dimensions = dimensions
        for count, dim in enumerate(dimensions):
            self._index[dim] = count
    
    def insert(self, entry):
        self._items.append(entry)

    def end_insert(self, output_column, output_sampling, binary_output=False):
        output_index = self._index[output_column]
        
        def items():
            for item in self._get_items():
                yield item[output_index]
                
        self._output_min = min(items())
        self._output_max = max(items())
        _LOG.info('output min = %s' % self._output_min)
        _LOG.info('output max = %s' % self._output_max)
        self._output_sampling = output_sampling
        self._binary_output = binary_output

    def fetch(self, item, dim):
        return item[self._index[dim]]

    def count(self):
        """Counts the number of rows in the table."""
        return len(self._get_items())

    def random_split(self, set_left, set_right):
        for item in self._get_items():
            random.choice([set_left, set_right]).insert(item)
            
    def get_dimensions(self):
        """Gets all defined dimensions"""
        return self._dimensions

    def median(self, dim):
        """
        Computes the median for a dimension
        """
        return self._get_median(dim)

    def entropy(self, dim):
        return self._get_entropy(dim)

    def sample_measures(self, dimension, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        index = self._index[dimension]
        sample_size = min(sample_size, self.count())
        return [item[index] for item in random.sample(self._get_items(), sample_size)]

    def split(self, dimension, split_value):
        """Split according to a given dimension and a split value.
        Returns a 3-uple of tables: one for values <= split_value, one for
        values > split_val and one for undef values of the dimension.

        @param dimension: dimension to split on
        @param split_value: split value

        """
        left_table = self._create_child_table()
        right_table = self._create_child_table()
        null_table = self._create_child_table()
        index = self._index[dimension]
        for entry in self._get_items():
            if entry[index] is None:
                null_table.insert(entry)
                
            elif entry[index] <= split_value:
                left_table.insert(entry)

            else:
                right_table.insert(entry)

        return left_table, right_table, null_table

    def to_csv(self, csv_file, selected=None, excluded=None):
        """
        Careful, that can be huge...
        """
        import csv
        dimensions = list()
        for dim in self.get_dimensions():
            if (selected is None or dim == selected) and dim != excluded:
                dimensions.append(dim)

        field_names = ['id'] + dimensions
        csv_writer = csv.DictWriter(csv_file, fieldnames=field_names, dialect='excel')
        csv_writer.writeheader()
        for item_id, item in enumerate(self._get_items()):
            row_data = dict()
            row_data['id'] = item_id
            for dim in dimensions:
                row_data[dim] = self.fetch(item, dim)

            csv_writer.writerow(row_data)

    def __repr__(self):
        return '[set of %d rows]' % self.count()
        
