import math
import argparse

from predict.decisiontree.training import TrainingSetFactory

def main(args):
    def in_oblique_rectangle(x0, y0, x1, y1, width, height, rotation=math.pi/3.0):
        # expressing x0, y0 in the coordinates of the rectangle
        # Step 1 - translation
        x0_t = x0 - x1
        y0_t = y0 - y1
        # Step 2 - rotation
        x0_tr = x0_t * math.cos(rotation) - y0_t * math.sin(rotation)
        y0_tr = x0_t * math.sin(rotation) + y0_t * math.cos(rotation)
        return x0_tr <= width and x0_tr >= 0 and y0_tr >= 0 and y0_tr <= height
        
    def oblique_rectangle_func(x0, y0):
        return (0.0, 1.0)[in_oblique_rectangle(x0, y0, -0.9, 0.1, 1.0, 1.0)]
    
    range_x = (-2.0, 2.0)
    range_y = (-2.0, 2.0)
    factory = TrainingSetFactory()
    missing_rate = float(args.missing_rate) / 100.0
    data = factory.train_x_y(oblique_rectangle_func, args.size, 
            range_x, range_y, target_name=args.target_column,
            missing_rate=missing_rate)
    
    data.to_csv(args.output, excluded=args.target_column)
    args.output.close()
    data.to_csv(args.check, selected=args.target_column)
    args.check.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generates test data for Random Forests',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    
    parser.add_argument('-o', '--output',
        type=argparse.FileType('w'),
        default='tests.csv',
        help='test samples')
    
    parser.add_argument('-c', '--check',
        type=argparse.FileType('w'),
        default='tests-check.csv',
        help='test samples with correct results for cross-checking regression output')
    
    parser.add_argument('-s', '--size',
        type=int,
        default=1000,
        help='number of test data to be generated')
    
    parser.add_argument('-m', '--missing-rate',
        type=int,
        default=10,
        help='desired rate of missing values in percent')
    
    parser.add_argument('-t', '--target-column',
        type=str,
        default='target',
        help='name of the ouput column')
    
    args = parser.parse_args()
    main(args)
