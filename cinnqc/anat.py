import os
import numpy as np
import subprocess

def tissue_seg(dataset, scan_number = None, subjects = None, run_brain_extract = True, bet_optional_args = ""):
    
    """
    Performs tissue class segmentation for structural data from the BIDS dataset. 
    Note, this function requires brain_extract to have been run. This is enabled by default.
    
    Parameters:
        dataset(object): cinnqc object for the BIDS dataset.
        scan_number(list): Scan numbers for anatomical data to be segmented.
        subjects(list): Subjects to have anatomical data segmented for.
        run_brain_extract(boolean): Run bet to extract brain before performing segmentation.
        bet_optional_args(string): Optional arguments for bet to optimise brain extraction
        
    Output:
        scan-{scan_number}_tissue-seg_mixeltype.nii.gz voxel-wise mixel value
        scan-{scan_number}_tissue-seg_pve_0.nii.gz csf voxel probability image
        scan-{scan_number}_tissue-seg_pve_1.nii.gz grey matter voxel probability image
        scan-{scan_number}_tissue-seg_pve_2.nii.gz white matter voxel probability
        scan-{scan_number}_tissue-seg_pveseg.nii.gz hard segmentation of csf grey matter and white matter
        scan-{scan_number}_tissue-seg_seg.nii.gz hard segmentation of csf grey matter and white matter
        
    Example:
        import cinnqc
        bidsdir = cinnqc.anat.tissue_seg(dataset, subjects = ['sub-001','sub-002','sub-003'])
    """
    
    
    # Get indicies for anatomical data if no scan numbers are provided
    if scan_number == None:      
        scan_number = dataset.output.loc[dataset.output['bids_subdir'].str.contains("anat", case=False)].index.tolist()        

    if subjects == None:
        subjects = dataset.subjects
        
    # Iterate over defined subjects and scans
    for subject in subjects:
        for scan in scan_number:
            
            if run_brain_extract:
                brain_extract(dataset, scan_number = scan, subjects = subject, optional_args = bet_optional_args)            
            
            # Check the type of anatomical image, this is passed to FAST to describe the type of image
            if dataset.output.loc[scan]['scan_type'].upper() == 'T1':
                img_type = '1'
            elif dataset.output.loc[scan]['scan_type'].upper() == 'T2':
                img_type = '2'
            elif dataset.output.loc[scan]['scan_type'].upper() == 'PD':
                img_type = '3'
            
            
            # Define input file (output from bet) and output file
            file = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_bet.nii.gz")
            outfile = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_tissue-seg")
            
            # Check if motion corrected file and parameters exist and run mcflirt using subprocess if either does not
            if not (os.path.isfile(f"{outfile}_seg.nii.gz") and 
                    os.path.isfile(f"{outfile}_pveseg.nii.gz") and 
                    os.path.isfile(f"{outfile}_pve_2.nii.gz") and 
                    os.path.isfile(f"{outfile}_pve_1.nii.gz") and 
                    os.path.isfile(f"{outfile}_pve_0.nii.gz") and 
                    os.path.isfile(f"{outfile}_mixeltype.nii.gz")):
                subprocess.run(["fast", "-t", img_type, "-o", outfile, file], stdout=subprocess.PIPE)
                
def brain_extract(dataset, scan_number = None, subjects = None, optional_args = ""):
    
    """
    Performs brain extraction for structural data from the BIDS dataset.
    
    Parameters:
        dataset(object): cinnqc object for the BIDS dataset.
        scan_number(list): Scan numbers for anatomical data to be brain extracted.
        subjects(list): Subjects to have anatomical brain extracted for.
        optional_args(string): Optional arguments for bet to optimise brain extraction
        
    Output:
        scan-{scan_number}_bet.nii.gz brain extracted anatomical image
        scan-{scan_number}_bet_mask.nii.gz brain extracted anatomical image mask       
        
    Example:
        import cinnqc
        bidsdir = cinnqc.anat.brain_extract(dataset, subjects = ['sub-001','sub-002','sub-003'])
    """
    
    
    # Get indicies for anatomical data if no scan numbers are provided
    if scan_number == None:      
        scan_number = dataset.output.loc[dataset.output['bids_subdir'].str.contains("anat", case=False)].index.tolist()
    elif type(scan_number) == int:
        scan_number = [scan_number]
        
    if subjects == None:
        subjects = dataset.subjects
    elif type(subjects) == str:
        subjects = [subjects]
        
    # Iterate over defined subjects and scans
    for subject in subjects:
        for scan in scan_number:
                        
            # Check if session is defined for this scan and generate file path
            file = dataset._get_filepath(subject, scan)
                
            outfile = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_bet")
            
            # run brain extraction
            subprocess.run(["bet", file, outfile, "-m", optional_args], stdout=subprocess.PIPE)