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
        else:
            self.output = pd.read_csv(self.output_path, index_col='scan_number')
            self._add_subjects()
            
        self.save_output()
            
    def _add_subjects(self):
        """
        Updates the subjects in the output file in case new particicipants have been added
        
        Returns:
            an update to self.output with columns for all participants in the BIDS directory.
        """
        for subj in self.subjects:
            if subj not in self.output.columns:
                self.output[subj] = ""
                
        self.save_output()
                
    def _append_output(self, subject, scan_number, note):
        """
        adds information about QC issues to a text file for each scan.

        Parameters:
            subject(string): The subject with the QC issue.
            scan_number(integer): The scan_number with the QC issue.
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
        
        Parameters:
            subject(string): subject who the scan will be checked for.
            scan_number(integer): scan number that will be checked to see if it exists.
            filepath(string): expected path to the file (optional).
            
        Returns:
            (Boolean) True if the file exists, false if it doesn't exist.
        """
        
        if filepath is None:
            filepath = self._get_filepath(subject, scan_number)
        
        if os.path.isfile(filepath):
            return True
        else:
            self._append_output(subject, scan_number, "This file does not exist")
            return False
        
    def _get_filepath(self, subject, scan_number):
        """
        gets path to a file for a given subject and scan number. This function is helpful as BIDS datasets with sessions vs those without name files in different ways and have sessions subdirectories.
        
        Parameters:
            subject(string): subject the filepath will be generated for.
            scan_number(integer): the scan number the filepath will be generated for
            
        Returns:
            filepath: path to the file for the given scan_number
        
        """
        if np.isnan(self.output.at[scan_number, 'session']):
            filepath = os.path.join(self.path, subject, f"{self.output.at[scan_number,'bids_subdir']}/{subject}{self.output.at[scan_number,'scan_suffix']}")
        else:
            filepath = os.path.join(self.path, subject, f"{self.output.at[scan_number,'session']}/{self.output.at[scan_number,'bids_subdir']}/{subject}_{self.output.at[scan_number,'session']}{self.output.at[scan_number,'scan_suffix']}")
            
        return filepath
                
    
    def check_dims(self, subjects = None, scan_number = None):
        """
        checks dimensions of scans for this dataset.

        Parameters:
            subject(string): The subject with the QC issue.
            scan_number(integer): The scan_number with the QC issue.
            
        Returns:

        Example:
        
        """
        if subjects == None:
            subjects = self.subjects
        if scan_number == None:
            scan_number = list(self.output.index.values)
            
        for subject in subjects:
            for scan in scan_number:
                filepath = self._get_filepath(subject, scan)
                    
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
        
        self.save_output()
                        
    def manual_fail(self, subject, scan_number, note = None):
        """
        manually fail qc for a given subject and scan number. note can be used as an option to provide a description for why the scan was failed, else a message "MANUAL FAIL - NO NOTE ADDED" will be appended.

        Parameters:
            subject(string): The subject that will have scan manually failed.
            scan_number(integer): The scan_number that will be failed.

        Returns:

        Example:

        """
        if note == None:
            note = "MANUAL FAIL - NO NOTE ADDED"

        self._append_output(subject, scan_number, note)
        self.output.at[scan_number, subject] = "EXCLUDE"
        self.save_output()
    
    def reset_qc(self, subject, scan_number):
        """
        manually resets qc for a given subject and scan number. This will include the txt file describing qc issues and the output dataframe

        Parameters:
            subject(string): The subject that will have scan manually failed.
            scan_number(integer): The scan_number that will be failed.

        Returns:

        Example:

        """
        output = open(os.path.join(self.path, f"derivatives/cinnqc/{subject}/scan_number_{scan_number}_notes.txt"),"w")
        output.write("")
        output.close
        
        self.output.at[scan_number, subject] = np.nan
        self.save_output()
    
    def save_output(self, output_path = None):
        """
        saves the output dataframe to a csv file

        Parameters:
            output_path(string): The path to where the csv file should be saved

        Returns:

        Example:

        """
        if output_path == None:
            output_path = self.output_path
            
        self.output.to_csv(output_path)
            
    def update_output_info(self, info = None):
        """
        updates scan parameter information given in the output pandas dataframe and csv file. info can be used to provide a path to a new file, or self.info will be used to update scan parameters. When updating your info file, please DO NOT ALTER PREVIOUSLY ASSIGNED SCAN_NUMBER.
        
        Parameters:
            info(string): Path to the csv file that describes the BIDS directory for QC.
            
        Returns:
        
        Example:
        
        """
        if info == None:
            info = self.info
        
        tmp_output = pd.read_csv(info, index_col='scan_number')
        for subj in self.subjects:
            if subj not in tmp_output.columns:
                tmp_output[subj] = ""        
    
        for idx in self.output.index.values:
            # check for any scan_number missing from new df that were in the old df and add them
            if idx not in tmp_output.index.values:
                test.output.loc[idx] = [""] * len(tmp_output.output.columns)
            # do the same for missing columns
            for col in self.output.columns:
                if col not in tmp_output.columns:
                    tmp_output[col] = ""
                tmp_output.loc[idx, col] = self.output.loc[idx, col]
        
        self.output = tmp_output
        self.save_output()