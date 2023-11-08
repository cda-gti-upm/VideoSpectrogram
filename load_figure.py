"""
Load figure save in pickle format
"""

import pickle
import argparse
import matplotlib.pyplot as plt


# Main program
if __name__ == "__main__":
    """
    Process input arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("figure_path")
    args = parser.parse_args()

    # Load figure
    fig = pickle.load(open(args.figure_path, 'rb'))
    plt.show()
