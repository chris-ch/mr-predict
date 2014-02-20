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
        
    def add_dimensions(self, names):
        dimensions = list()
        for name in names:
            dimensions.append(Dimension.make(name, context_key=self.key))
            self.dimensions_count += 1
        
        ndb.put_multi(dimensions)
        return dimensions
        
    def csv_import_header(self, csv_reader):
        header = next(csv_reader)
        return self.add_dimensions([column for column in header[1:]])
        
    def csv_import(self, csv_reader, dimensions):
        counter = 0
        samples = list()
        measures = 0
        for row in csv_reader:
            new_sample = create_row(row, self.key, dimensions)
            samples.append(new_sample)
            counter += 1
            if counter % 100 == 0:
                _LOG.info('%d rows processed' % counter)
            
            measures += len(new_sample.measures)
            self.measures_count += len(new_sample.measures)
                
        _LOG.info('saving a total of %d elements' % measures)
        ndb.put_multi(samples)
        self.put()
       
class Dimension(ndb.Model):
    """
    Represents one characteristic of a profile.
    """
    name = ndb.StringProperty(required=True)
    context = ndb.KeyProperty(kind=TrainingContext)
    
    @classmethod
    def make(cls, name, context_key):
        new_dimension = Dimension(name=name, context=context_key)
        return new_dimension
        
class Measure(ndb.Model):
    
    value = ndb.FloatProperty()
    dimension = ndb.KeyProperty(kind=Dimension, repeated=False)

class Sample(ndb.Model):
    """
    Represents one profile in the training universe.
    """
    sample_id = ndb.StringProperty(required=True)
    context = ndb.KeyProperty(kind=TrainingContext)
    measures = ndb.StructuredProperty(Measure, repeated=True)
    
    @classmethod
    def make(cls, sample_id, context_key):
        new_sample = Sample(sample_id=sample_id, context=context_key)
        return new_sample
        
def create_row(row, context_key, dimensions):
    sample_id = row[0]
    new_sample = Sample.make(sample_id, context_key)
    measures = create_measures(dimensions, row[1:])
    new_sample.measures = measures
    return new_sample

def create_measures(dimensions, row):
    new_measures = list()
    for count, cell in enumerate(row):
        try:
            value = float(cell)
            new_measure = Measure(value=value, dimension=dimensions[count].key)
            new_measures.append(new_measure)
            
        except ValueError:
            _LOG.debug('failed to convert value "%s" (ignoring)' % cell)
            
    return new_measures

