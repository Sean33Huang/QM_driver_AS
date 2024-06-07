"""
This program focus on analyze the references.
"""
from src.analysis.Radiator.RadiatorSetAna import main_analysis, get_references_from_ResultJson, save_ref


""" Manually fill in """
target_q = 'q3'    
sample_folder = "AS_radiator"     # the previous folder from conditional_folder
conditions = "WS"          # the previous folder from temperature folder 

# ? Save the references from a mK set
ref_info = {"before":{"save_ref_to_json":True, "mK_folder_path":"/Users/ratiswu/Downloads/AS_radiator/WS/4K"},"recover":{"save_ref_to_json":False, "mK_folder_path":""}}

# save reference
for ref_type in ref_info:
    if ref_info[ref_type]["save_ref_to_json"]:
        if ref_info[ref_type]["mK_folder_path"] != "":
            main_analysis(target_q, ref_info[ref_type]["mK_folder_path"])
            ref_dict = get_references_from_ResultJson(ref_info[ref_type]["mK_folder_path"])
            save_ref(ref_dict,target_q,sample_name=sample_folder,conditional_name=conditions,ref_type=ref_type)