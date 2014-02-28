import pstats
import sys

p = pstats.Stats(sys.argv[1])
p.sort_stats(-1).print_stats()
