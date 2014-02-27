import csv
import sys

def main(args):
    filename = args[0]
    with open(filename, 'rb') as csvfile:
        rows = csv.reader(csvfile)
        output = csv.writer(sys.stdout)
        headers = next(rows)
        output.writerow(headers)
        for row in rows:
            target = float(row[-1])
            row[-1] = (0, 1)[ target > 1.0 ]
            output.writerow(row)

if __name__ == '__main__':
    main(sys.argv[1:])
