"""
Basic functions that will be used by the package
"""

from glob2 import glob
import os
import pandas as pd
import numpy as np

class bids:
    """
    creates an object from the BIDS directory for this dataset.
    
    Parameters:
        path(string): Path to the BIDS directory for the dataset that will be QC'd.
        info(string): Path to the csv file that describes the BIDS directory for QC.
        
    Returns:
        self.path(string): Path to the BIDS directory for the dataset that will be QC'd.
        self.info(string): Path to the csv file that describes the BIDS directory for QC.
        self.subjects(list): Participants in the BIDS dataset.
        self.sess(list): Sessions in the BIDS dataset.
        
    Example:
        import cinnqc
        bidsdir = cinnqc.bids('/cinnqc/examples/BIDS/','/cinnqc/examples/bidsinfo_task.csv')
    """
    
    def __init__(self, path, info):
        if not os.path.isdir(path):
            raise Exception("Incorrect path to BIDS directory")
        os.path.isfile(info)
              
        self.path = path
        self.info = info
        self.subjects=[os.path.basename(s) for s in sorted(glob(os.path.join(self.path, 'sub-*'))) if os.path.isdir(s)]
        sess = pd.read_csv(self.info); sess = sess['session'].fillna(np.nan).unique()
        if np.all(np.isnan(sess)):
            self.sess = None
        else:
            self.sess = sess[~np.isnan(sess)]

