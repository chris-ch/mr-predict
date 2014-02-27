import csv
import sys
from collections import defaultdict

def as_number(s):
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
        
MIN = 0
MAX = 1
MEAN = 2
UNIQUE = 3
NA = 4
    
def csv_statistics(csvfile, has_header, categories_limit, filename=None, keepers=None, out=sys.stdout):
        
    def init_stats():
        return [None, None, None, set(), 0]
    
    if keepers is None:
        new_keepers = set()
        
    else:
        new_keepers = set(keepers)
    
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    rows = csv.reader(csvfile, dialect)
    if has_header:
        headers = next(rows)
        stats = dict()
        for header in headers:
            stats[header] = init_stats()
            
    else:
        # using column position as id
        stats = defaultdict(lambda: init_stats)
            
    def col_key(index):
        if not has_header: return index
            
        else:
            return headers[index]
            
    for row_count, row in enumerate(rows, start=1):
        for index, cell in enumerate(row):
            col_stats = stats[col_key(index)]
            if as_number(cell) is None:
                # not a number
                col_stats[NA] += 1
                value = None
                
            else:
                # number
                if as_int(cell) is None:
                    new_keepers.add(col_key(index))
                    value = as_number(cell)
                    
                else:
                    value = as_int(cell)
                    
                if not col_stats[MIN] or value < col_stats[MIN]:
                    col_stats[MIN] = value
                    
                if not col_stats[MAX] or value > col_stats[MAX]:
                    col_stats[MAX] = value
                    
                if not col_stats[MEAN]:
                    col_stats[MEAN] = value
                    
                col_stats[MEAN] += value
                
            if len(col_stats[UNIQUE]) < categories_limit:
                col_stats[UNIQUE].add(value)
            
    unicity_check = dict()
    for col_id in stats.keys():
        # adjusting mean
        stats[col_id][MEAN] /= row_count
        
        # checking column unicity
        col_min = stats[col_id][MIN]
        col_max = stats[col_id][MAX]
        col_mean = stats[col_id][MEAN]
        col_na = stats[col_id][NA]
        unicity_check[col_id] = (col_min, col_max, col_mean, col_na)
    
    inv_unicity_check = {v:k for k, v in unicity_check.items()}
    unique_columns = inv_unicity_check.values()
    # resets input file
    csvfile.seek(0)
    
    return new_keepers, unique_columns, headers, stats
    
def generate_output(csvfile, has_header, categories_limit, keepers, unique_columns, headers, stats):
    
    def col_key(index):
        if not has_header: return index
            
        else:
            return headers[index]
            
    dialect = csv.Sniffer().sniff(csvfile.read(1024))
    csvfile.seek(0)
    rows = csv.reader(csvfile, dialect)
    writer = csv.writer(sys.stdout)
    if has_header:
        row = next(rows)
        values = list()
        for index, cell in enumerate(row):
            col_id = col_key(index)
            if col_id not in unique_columns: continue
            if col_id in keepers:                
                values.append(cell)
                
            elif len(stats[col_id][UNIQUE]) < categories_limit:
                # splits column into N indicator functions
                values += [cell + '_' + str(val) for val in stats[col_id][UNIQUE]]
                
            else:
                values.append(cell)
            
        writer.writerow(values)
            
    for row in rows:
        values = list()
        for index, cell in enumerate(row):
            col_id = col_key(index)
            if col_id not in unique_columns: continue
            if col_id not in keepers and len(stats[col_id][UNIQUE]) < categories_limit:
                # splits column into N indicator functions
                values += [(0, 1)[cell == str(val)] for val in stats[col_id][UNIQUE]]
            else:
                if as_number(cell) is not None:
                    value = as_number(cell)
                    
                else:
                    value = stats[col_id][MEAN]
                    
                values.append(value)
                    
        writer.writerow(values)
          
def main(filename=None):
        
    # uses column position if header not available
    has_header = True
    
    # max number beyond which dimension is not considered as a category
    categories_limit = 50
    
    if filename:
        csvfile = open(filename, 'rb')
        
    else:
        csvfile = sys.stdin
        
    keepers, unique_columns, headers, stats = csv_statistics(csvfile, has_header, categories_limit, filename=filename, keepers=('loss', ))
    
    generate_output(csvfile, has_header, categories_limit, keepers, unique_columns, headers, stats)
    
if __name__ == '__main__':
	filename = None
	if len(sys.argv) > 1:
	    filename = sys.argv[1]
	    
	main(filename)
	
