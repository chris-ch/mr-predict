import logging

from google.appengine.ext import ndb
from google.appengine.ext import deferred

_LOG = logging.getLogger('models')

class TrainingContext(ndb.Model):
    """
    Binds elements of a training set together.
    """
    
    user_id = ndb.StringProperty(required=True)
    name = ndb.StringProperty(required=True)
    source_filename = ndb.StringProperty()
    measures_count = ndb.IntegerProperty(required=True, default=0)
    dimensions_count = ndb.IntegerProperty(required=True, default=0)
    
    @classmethod
    def find_new_name(cls, user_id):
        new_name = 'New context'
        if cls.query().count() > 0:
            names = cls.query(TrainingContext.user_id == user_id).fetch(projection=[cls.name])
            _LOG.info('all names: %s' % str(names))
            new_name = 'New context %s' % str(len(names))
        
        return new_name
        
    @classmethod
    def clear(cls, context):
        measures = Measure.query(Measure.context == context.key)
        for measure in measures:
            measure.key.delete()
            
        samples = Sample.query(Sample.context == context.key)
        for sample in samples:
            sample.key.delete()
            
        dimensions = Dimension.query(Dimension.context == context.key)
        for dimension in dimensions:
            dimension.key.delete()

        context.key.delete()
        
    @classmethod
    def get_or_create(cls, name, source_filename='unspecified'):
        context = cls(name=name, source_filename=source_filename)
        context.put()
        
    def add_dimension(self, name):
        new_dimension = Dimension(name=name, context=self.key)
        new_dimension_key = new_dimension.put()
        self.dimensions_count += 1
        self.put()
        return new_dimension_key
        
    def csv_import_header(self, csv_reader):
        dimensions = list()
        for column in next(csv_reader)[1:]:
            _LOG.info('creating dimension "%s"' % str(column))
            new_dimension_key = self.add_dimension(column)
            dimensions.append(new_dimension_key)
            
        return dimensions
        
    def csv_import(self, csv_reader, dimensions):
        counter = 0
        samples = list()
        measures = list()
        for row in csv_reader:
            (new_sample, new_measures) = save_row(row, self.key, dimensions)
            samples.append(new_sample)
            measures += new_measures
            counter += 1
            if counter % 100 == 0:
                _LOG.info('%d rows processed' % counter)
        for sample in samples:
            sample.put()
            
        for measure in measures:
            measure.put()
       
class Dimension(ndb.Model):
    """
    Represents one characteristic of a profile.
    """
    context = ndb.KeyProperty(kind='TrainingContext', required=True)
    name = ndb.TextProperty(required=True, indexed=True)
    
    @classmethod
    def get_or_create(cls, name, context=None):
        """
        Makes sure a default context is created if required
        """
        if not context:
            context_key = TrainingContext.get_or_create(name='unspecified')
            context = context_key.get()
            
        return context.add_dimension(name)

def save_row(row, context_key, dimensions):
            sample_id = row[0]
            new_sample = Sample(context=context_key, name=sample_id)
            measures = save_measures(new_sample, dimensions, row[1:])
            return (new_sample, measures)

def save_measures(sample, dimensions, row):
        context = self.context.get()
        new_measures = list()
        for count, cell in enumerate(row):
            try:
                value = float(cell)
                new_measure = Measure(context=self.context,
                    dimension=dimensions[count],
                    sample=self.key,
                    value=value
                    )
                new_measures.append(new_measure)
                context.measures_count += 1
                
            except ValueError:
                _LOG.debug('failed to convert value "%s" (ignoring)' % cell)
                
        return measures

class Sample(ndb.Model):
    """
    Represents one profile in the training universe.
    """
    context = ndb.KeyProperty(kind='TrainingContext')
    name = ndb.TextProperty(indexed=False)
    
    def add_measures(self, dimensions, values):
        context = self.context.get()
        new_measures = save_measures(self, dimensions, values)
        ndb.put_multi(new_measures)
        context.put() # updates counters
    
    def add_measure(self, dimension_key, value):
        self.add_measures([dimension_key], [value])

class Measure(ndb.Model):
    context = ndb.KeyProperty(kind='TrainingContext', required=True)
    value = ndb.FloatProperty(indexed=False)
    dimension = ndb.KeyProperty(kind='Dimension', required=True)
    sample = ndb.KeyProperty(kind='Sample', required=True)
    
