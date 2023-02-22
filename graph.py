import json
import sys

import matplotlib.pyplot as plt
import numpy as np

def make_graph(files):

    indexes = [ n for n in range(1000) ]

    for file_name in files:
        with open(file_name) as f:
            data = json.loads(f.read())

        plt.plot(np.array(indexes), np.array(data), label=file_name[9:].split(".")[0])
    plt.title(f"Raw rec rankings")
    plt.legend()
    plt.savefig("rankings.png", dpi=300)

make_graph(sys.argv[1:])
