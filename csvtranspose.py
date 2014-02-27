import csv
import sys

def main():
    reader = csv.reader(sys.stdin)
    next(reader)
    cols = []
    for row in reader:
        cols.append(row)
    
    writer = csv.writer(sys.stdout)
    for i in xrange(len(max(cols, key=len))):
        writer.writerow([(c[i] if i<len(c) else '') for c in cols])
        
if __name__ == '__main__':
	main()
