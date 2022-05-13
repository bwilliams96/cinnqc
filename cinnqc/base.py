"""
Basic functions that will be used by the package
"""

from glob2 import glob
import os
import pandas as pd
import numpy as np
from pathlib import Path

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
        self.output(pandas dataframe): Pandas dataframe containing output file from cinnqc
        self.output_path: Path to csv file of Pandas dataframe
        
    Example:
        import cinnqc
        bidsdir = cinnqc.bids('/cinnqc/examples/BIDS/','/cinnqc/examples/bidsinfo_task.csv')
    """
    
    def __init__(self, path, info):
        
        #Check if bids directory and info file exist
        if not os.path.isdir(path):
            raise Exception("Incorrect path to BIDS directory")
        os.path.isfile(info)
              
        self.path = path
        self.info = info
        
        #Get subjects from the bids directory
        self.subjects=[os.path.basename(s) for s in sorted(glob(os.path.join(self.path, 'sub-*'))) if os.path.isdir(s)]
        
        #Get session information for the bids dataset from the info file
        sess = pd.read_csv(self.info); sess = sess['session'].fillna(np.nan).unique()
        if np.all(np.isnan(sess)):
            self.sess = None
        else:
            self.sess = sess[~np.isnan(sess)]
            
        #Check if output directories exists in derivatives directory for each subject and create one if not
        for subj in self.subjects:
            if not os.path.isdir(os.path.join(self.path, f"derivatives/cinnqc/{subj}")):
                    Path(os.path.join(self.path, f'derivatives/cinnqc/{subj}')).mkdir(parents=True, exist_ok=True)
                    
        #Check if there is an existing output csv file and create one if not
        self.output_path = os.path.join(self.path, f"derivatives/cinnqc/cinnqc_output.csv")
        if not os.path.isfile(self.output_path):
            self.output = pd.read_csv(self.info)
            self.output = self.output.reindex(columns = self.output.columns.tolist() + self.subjects)
            self.output.to_csv(self.output_path, index=False)
        else:
            self.output = pd.read_csv(self.output_path)
            self._add_subjects()
            self.output.to_csv(self.output_path, index=False)
            
    def _add_subjects(self):
        """
        Updates the subjects in the output file in case new particicipants have been added
        """
        for subj in self.subjects:
            if subj not in self.output.columns:
                self.output[subj] = ""

        
        