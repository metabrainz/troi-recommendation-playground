#!/usr/bin/env python3

import click
import copy
import io
import subprocess
import ujson

from troi import Entity, EntityEnum
from troi.datasource.lb_stats import ListenBrainzStatsDataSource as Stats
import config

def test():
    stats = Stats("rob", "recording", "week")
    print(stats.get())

if __name__ == "__main__":
    test()
