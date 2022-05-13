"""
Basic functions that will be used by the package
"""

from glob2 import glob
import os
import pandas as pd
import numpy as np
from pathlib import Path
import nibabel as nib

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
            self.output = pd.read_csv(self.info, index_col='scan_number')
            self.output = self.output.reindex(columns = self.output.columns.tolist() + self.subjects)
            self.output.to_csv(self.output_path)
        else:
            self.output = pd.read_csv(self.output_path, index_col='scan_number')
            self._add_subjects()
            self.output.to_csv(self.output_path)
            
    def _add_subjects(self):
        """
        Updates the subjects in the output file in case new particicipants have been added
        """
        for subj in self.subjects:
            if subj not in self.output.columns:
                self.output[subj] = ""
                
    def _append_output(self, subject, scan_number, note):
        """
        adds information about QC issues to a text file for each scan.

        Parameters:
            subject(string): The subject with the QC issue.
            scan_number(string): The scan_number with the QC issue.
            note(string): The note to be added to the text file.

        Returns:
            A text file (BIDS/derivatives/cinnqc/{subject}/scan_number_{scan_number}_notes.txt) describing the QC issue.
        """
        
        output = open(os.path.join(self.path, f"derivatives/cinnqc/{subject}/scan_number_{scan_number}_notes.txt"),"a+")
        output.write(note + "\n")
        output.close

    
    def _check_exists(self, subject, scan_number, filepath=None):
        """
        Checks a given scan_number exists for a given subject
        """
        
        if filepath is None:
            if np.isnan(self.output.at[scan_number,'session']):
                filepath = os.path.join(self.path, subject, f"{self.output.at[scan_number,'bids_subdir']}/{subject}{self.output.at[scan_number,'scan_suffix']}")
            else:
                filepath = os.path.join(self.path, subject, f"{self.output.at[scan_number,'session']}/{self.output.at[scan_number,'bids_subdir']}/{subject}_{self.output.at[scan_number,'session']}{self.output.at[scan_number,'scan_suffix']}")
        
        if os.path.isfile(filepath):
            return True
        else:
            self._append_output(subject, scan_number, "This file does not exist")
            return False
        
    
    def check_dims(self, subjects = None, scan_number = None):
        """
        checks dimensions of scans for this dataset.

        Parameters:
            subject(string): The subject with the QC issue.
            scan_number(string): The scan_number with the QC issue.
            
        Returns:

        Example:
        
        """
        if subjects == None:
            subjects = self.subjects
        if scan_number == None:
            scan_number = list(self.output.index.values)
            
        for subject in subjects:
            for scan in scan_number:
                if np.isnan(self.output.at[scan,'session']):
                    filepath = os.path.join(self.path, subject, f"{self.output.at[scan,'bids_subdir']}/{subject}{self.output.at[scan,'scan_suffix']}")
                else:
                    filepath = os.path.join(self.path, subject, f"{self.output.at[scan,'session']}/{self.output.at[scan,'bids_subdir']}/{subject}_{self.output.at[scan,'session']}{self.output.at[scan,'scan_suffix']}")
                    
                if self._check_exists(subject, scan, filepath):
                    img = nib.load(filepath)
                    if len(img.shape) == 3:
                        for idx, dim in zip([0,1,2], ["dim1","dim2","dim3"]):
                            if self.output.at[scan,dim] != img.shape[idx]:
                                self._append_output(subject, scan, f"Image was expective to have size {self.output.at[scan,dim]} for {dim}, but returned size {img[idx]}")
                                self.output.at[scan,subject] = "EXCLUDE" 
                    elif len(img.shape) == 4:
                        for idx, dim in zip([0,1,2,3], ["dim1","dim2","dim3","dim4"]):
                            if self.output.at[scan,dim] != img.shape[idx]:
                                self._append_output(subject, scan, f"Image was expective to have size {self.output.at[scan,dim]} for {dim}, but returned size {img[idx]}")
                                self.output.at[scan,subject] = "EXCLUDE" 
                    else:
                        self._append_output(subject, scan, f"Image has {len(img.shape)} dimensions")
                    