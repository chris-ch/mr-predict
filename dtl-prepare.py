import random
import argparse
import csv

from predict.decisiontree.training import TrainingSetFactory

def file_len(f):
    for i, l in enumerate(f):
        pass

    f.seek(0)
    return i + 1

def main(args):
    # splits the input file in various buckets for testing quality of training
    input_file = args.csv_input_file
    input_file_size = file_len(input_file)

    leftover_size = int(float(args.leftover_ratio_pct) * input_file_size / 100.0)
    leftovers = random.sample(xrange(input_file_size), leftover_size)

    # splitting input rows
    output_file = open(args.output, 'w')
    check_file = open(args.check, 'w')
    training_file = open(args.training, 'w')

    input_rows = csv.reader(input_file)
    first_line = next(input_rows)
    headers = first_line[1:]
    index_target = headers.index(args.target_column)
    id_column = first_line[0]
    for index, row in enumerate(input_rows):
        if index in leftovers:
            # this becomes a test sample
            columns = row[1:]
            values = [column for count, column in enumerate(columns)
                if count != index_target]

            output_file.write(','.join(values))

            # cross-checks
            check_file.write(','.join([row[0], columns[index_target]]))

        else:
            # this becomes a training sample
            training_file.write(','.join(row))

    output_file.close()
    check_file.close()
    training_file.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates test data for Random Forests using existing samples',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-o', '--output',
        type=str,
        default='tests.csv',
        help='test samples')

    parser.add_argument('-c', '--check',
        type=str,
        default='tests-check.csv',
        help='test samples with correct results for cross-checking regression output')

    parser.add_argument('-x', '--training',
        type=str,
        default='training.csv',
        help='training samples')

    parser.add_argument('-r', '--leftover-ratio-pct',
        type=int,
        default=20,
        help='size of leftover set in percent, relative to whole training file size')

    parser.add_argument('csv_input_file',
        type=argparse.FileType('r'),
        help='CSV file (including header) with list of samples. First column serves as id for the samples')

    parser.add_argument('-t', '--target-column',
        type=str,
        default='target',
        help='name of the ouput column')

    args = parser.parse_args()
    main(args)

