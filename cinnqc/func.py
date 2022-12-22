import os
import numpy as np
import subprocess
from cinnqc.anat import *

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
        example_func image used as reference for motion correction
        
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
                      
            # Check if session is defined for this scan and generate file path
            file = dataset._get_filepath(subject, scan)
                
            outfile = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_motion-corrected")
            outfile_examplefunc = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_example-func")
            
            # Check if motion corrected file and parameters exist and run mcflirt using subprocess if either does not
            if not (os.path.isfile(f"{outfile}.nii.gz") and os.path.isfile(f"{outfile}.par")):
                subprocess.run(["mcflirt", "-in", file, "-out", outfile, "-plots", "-refvol", "0"], stdout=subprocess.PIPE)
                subprocess.run(["fslroi", file, outfile_examplefunc, "0", "1"], stdout=subprocess.PIPE)

                
def epi_reg(dataset, anat_scan_number, epi_scan_number = None, subjects = None):
    
    """
    Performs registration functional data to structural data.
    
    Parameters:
        dataset(object): cinnqc object for the BIDS dataset.
        epi_scan_number(list): Scan numbers for functional data to be registered.
        anat_scan_number(int): Scan numbers for anatomical image used for registration.
        subjects(list): Subjects to have functional data motion corected for.
        
    Output:
        Affine transforms between the anatomical and functional image
        example_func image used as reference for motion correction
        brain mask in functional space
        
    Example:
        cinnqc.func.epi_reg(test, 1, epi_scan_number = [2], subjects = ['sub-001'])
    """
    
    
    # Get indicies for functional data if no scan numbers are provided
    if epi_scan_number == None:      
        epi_scan_number = dataset.output.loc[dataset.output['bids_subdir'].str.contains("func", case=False)].index.tolist()        

    if subjects == None:
        subjects = dataset.subjects
        
    # Iterate over defined subjects and scans
    for subject in subjects:
        for scan in epi_scan_number:
                            
            # check if bet and tissue segmenation have been performed for the structural image
            wm_seg = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{anat_scan_number}_tissue-seg_pve_2.nii.gz")
            bet_img = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{anat_scan_number}_bet.nii.gz")
            bet_mask = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{anat_scan_number}_bet_mask.nii.gz")
            if not (os.path.isfile(wm_seg)):
                if not (os.path.isfile(bet_img)):
                    tissue_seg(dataset, scan_number = [anat_scan_number], subjects = [subject])
                else:
                    tissue_seg(dataset, scan_number = [anat_scan_number], subjects = [subject], run_brain_extract = False)
            elif not (os.path.isfile(bet_img)):
                brain_extract(dataset, scan_number = [anat_scan_number], subjects = [subject])

            # get path to anatomical image
            
            anat = dataset._get_filepath(subject, anat_scan_number)
                
            # Check if example func image has been generated and make it if not
            examplefunc = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_example-func.nii.gz")
            if not (os.path.isfile(examplefunc)):
                if np.isnan(dataset.output['session'][scan]):
                    file = dataset._get_filepath(subject, scan)
                
                subprocess.run(["fslroi", file, examplefunc, "0", "1"], stdout=subprocess.PIPE)
                                  
            
            outprefix = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_epi-reg")
                      
            # run registration
            subprocess.run(["epi_reg", f"--epi={examplefunc}", f"--t1={anat}", f"--t1brain={bet_img}", f"--out={outprefix}", f"--wmseg={wm_seg}"], stdout=subprocess.PIPE)
            
            # apply transformation to brain mask to convert it to func image space
            subprocess.run(["convert_xfm", "-omat", f"{outprefix}-anat2func.mat", "-inverse", f"{outprefix}.mat"], stdout=subprocess.PIPE)
            subprocess.run(["flirt", "-in", bet_mask, "-ref", examplefunc, "-out", f"{outprefix}-brain_mask.nii.gz", "-init", f"{outprefix}-anat2func.mat", "-applyxfm"], stdout=subprocess.PIPE)
            subprocess.run(["fslmaths", f"{outprefix}-brain_mask.nii.gz", "-thr", "0.5", "-bin", os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_brain_mask.nii.gz")], stdout=subprocess.PIPE)
            os.remove(f"{outprefix}-brain_mask.nii.gz")
            os.remove(f"{outprefix}_fast_wmedge.nii.gz")
            os.remove(f"{outprefix}_fast_wmseg.nii.gz")
            os.rename(f"{outprefix}.mat", f"{outprefix}-func2anat.mat")
            
def pyfmriqc(pyfmriqc_path, dataset, anat_scan_number, epi_scan_number = None, subjects = None):
    
    """
    Performs registration functional data to structural data.
    
    Parameters:
        pyfmriqc_path(string): path to the pyfmriqc.py file #NOTE, HOW CAN I MAKE THIS MORE ERGONOMIC? 
        dataset(object): cinnqc object for the BIDS dataset.
        anat_scan_number(int): Scan number for the anatomical image assocaited with the functional image to be QC'd.
        epi_scan_number(list): Scan numbers for functional data to be QC'd.
        subjects(list): Subjects to have functional data QC'd.
        
    Output:
        Directory in subject's CINNQC derivatives directory with the pyfMRIqc output
        
    Example:
        cinnqc.func.pyfmriqc(/path/to/pyfmriqc.py, dataset, 1, epi_scan_number = [2], subjects = ['sub-001'])
    """
    
    
    # Get indicies for functional data if no scan numbers are provided
    if epi_scan_number == None:      
        epi_scan_number = dataset.output.loc[dataset.output['bids_subdir'].str.contains("func", case=False)].index.tolist()        

    if subjects == None:
        subjects = dataset.subjects
        
    # Iterate over defined subjects and scans
    for subject in subjects:
        for scan in epi_scan_number:
            # set paths to relevant files for pyfMRIqc
            func_mc = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_motion-corrected.nii.gz")
            func_mc_par = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_motion-corrected.par")
            func_mask = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/scan-{scan}_brain_mask.nii.gz")
            pyfmriqc_dir = os.path.join(dataset.path, f"derivatives/cinnqc/{subject}/pyfmriqc")
                          
            if dataset._check_exists(subject, scan):
                
                if not (os.path.isfile(func_mc)) or (os.path.isfile(func_mc_par)):
                    motion_correct(dataset, scan_number = [scan], subjects = [subject])
                
                if not (os.path.isfile(func_mask)):
                    epi_reg(dataset, anat_scan_number, epi_scan_number = [scan], subjects = [subject])
                
                if not (os.path.exists(pyfmriqc_dir)):
                    os.mkdir(pyfmriqc_dir)
                subprocess.run(["python", pyfmriqc_path, "-n", func_mc, "-s", str(25), "-k", func_mask, "-m", func_mc_par, "-o", pyfmriqc_dir], stdout=subprocess.PIPE)