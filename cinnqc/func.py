import os
import numpy as np
import subprocess

def motion_correct(dataset, scan_number = None, subjects = None):
    
    """
    Performs motion correction for functional data from the BIDS dataset.
    
    Parameters:
        dataset(object): cinnqc object for the BIDS dataset.
        scan_number(list): Scan numbers for functional data to be motion corrected.
        subjects(list): Subjects to have functional data motion corected for.
        
    Output:
        Motion corrected data in the cinnqc BIDS derivative directory for the specified scans and subjects
        Motion parameters in the cinnqc BIDS derivative directory for the specified scans and subjects 
        
    Example:
        import cinnqc
        bidsdir = cinnqc.func.motion_correct(dataset, subjects = ['sub-001','sub-002','sub-003'])
    """
    
    
    # Get indicies for functional data if no scan numbers are provided
    if scan_number == None:      
        scan_number = dataset.output.loc[dataset.output['bids_subdir'].str.contains("func", case=False)].index.tolist()        

    if subjects == None:
        subjects = dataset.subjects
        
    # Iterate over defined subjects and scans
    for subject in subjects:
        for scan in scan_number:
            
            scan_suffix = dataset.output['scan_suffix'][scan]
            
            # Check if session is defined for this scan and generate file path
            if np.isnan(dataset.output['session'][scan]):
                file = os.path.join(dataset.path, f"{subject}/func/{subject}{scan_suffix}")
            else:
                session = dataset.output['session'][scan]
                file = os.path.join(dataset.path, f"{subject}/{session}/func/{subject}_{session}{scan_suffix}")
                
            outfile = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_motion-corrected")
            
            # Check if motion corrected file and parameters exist and run mcflirt using subprocess if either does not
            if not (os.path.isfile(f"{outfile}.nii.gz") and os.path.isfile(f"{outfile}.par")):
                subprocess.run(["mcflirt", "-in", file, "-out", outfile, "-plots"], stdout=subprocess.PIPE)