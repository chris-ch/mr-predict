#
# -*- coding: utf-8 -*-
#
import logging
_LOG = logging.getLogger('training')

import random
from collections import defaultdict

class TrainingSetFactory(object):

    def train_csv(self, input_file, target_name='target'):
        import csv
        ts = TrainingSet()
        input_data = csv.reader(input_file, delimiter=',')
        header = next(input_data)[1:]
        assert target_name in header, 'target column "%s" is missing in input dataset' % target_name
        for columns in input_data:
            row = {}
            for index, cell in enumerate(columns[1:]):
                try:
                    row[header[index]] = float(cell)

                except ValueError:
                    # fine, simply ignore
                    pass

            _LOG.debug('inserting %s' % str(row))
            ts.insert(row)

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
        self.items = dict()
        self._statistics = dict()

    def insert(self, entry):
        row_id = len(self.items)
        self.items[row_id] = defaultdict(lambda: None)
        for key in entry.keys():
            if not key in self._dimensions:
                self._dimensions.append(key)

            self.items[row_id][key] = entry[key]

    def get_dimensions(self):
        """Get all table attributes."""
        return self._dimensions

    def count(self):
        """Counts the number of rows in the table."""
        return len(self.items)

    def count_not_null(self, dim):
        """Counts the number of rows in the table."""
        return len([item for item in self.items.itervalues() if item[dim] is not None])

    def median(self, dim):
        """
        Computes the median for a dimension
        """
        assert len(self.items) > 0, 'Trying to compute median of an empty set'
        return self.statistics(dim)[2]

    def variance(self, dim):
        return self.statistics(dim)[1]

    def statistics(self, dim):
        """
        Computes the statistics (mean, variance) for a dimension
        """
        assert len(self.items) > 0, 'Trying to compute variance of an empty set'
        if not self._statistics.has_key(dim):
            total = 0.0
            total_squares = 0.0
            values = list()
            for row in self.items.itervalues():
                if row[dim] is not None:
                    total += row[dim]
                    total_squares += row[dim]**2
                    values.append(row[dim])
                
            if len(values) == 0:
                return (None, None, None)
    
            values.sort()
            median = None
            if len(values) & 1:
                # odd number of items
                median = values[len(values) / 2]
                
            else:
                #even number of items
                median = 0.5 * (values[len(values) / 2 - 1] + values[len(values) / 2])
            
            mean = float(total) / len(values)
            variance = float(total_squares) / len(values) - mean**2
            self._statistics[dim] = (mean, variance, median)
            
        return self._statistics[dim]

    def sample_rows(self, sample_size):
        """Sample table rows uniformly at random."""
        assert len(self.items) > 0, 'Trying to sample an empty table'
        return [self.items[random.randint(0, len(self.items) - 1)]
                for i in range(sample_size)]

    def sample_measures(self, dimension, sample_size):
        """
        Samples uniformly at random from the set of values of a dimension.

        @param dimension: the dimension
        @param sample_size: number of values to sample

        """
        return [row[dimension] for row in self.sample_rows(sample_size)]

    def split(self, dimension, split_val):
        """Split according to a given dimension and a split value.
        Returns a 3-uple of tables: one for values <= split_val, one for
        values > split_val and one for undef values of the dimension.

        dimension -- dimension to split on
        split_val -- split value

        """
        left_table = TrainingSet()
        right_table = TrainingSet()
        null_table = TrainingSet()
        for entry in self.items.itervalues():
            if not dimension in entry.keys():
                null_table.insert(entry)

            elif entry[dimension] <= split_val:
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
        for item_id in self.items:
            row_data = dict()
            row_data['id'] = item_id
            for dim in dimensions:
                row_data[dim] = self.items[item_id][dim]

            csv_writer.writerow(row_data)


    def __str__(self):
        return self.to_csv()

