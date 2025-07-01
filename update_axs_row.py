import pandas as pd

# Define file paths
large_missing_path = r'C:\Users\david\david-py\ourstox6\pre_filled_stocks\missing_data\large_missing.csv'

# Data for AXS
axs_data = {
    'description': "AXIS Capital Holdings Limited is a global provider of specialty insurance and reinsurance solutions, headquartered in Pembroke, Bermuda. The company operates through its two primary segments: AXIS Insurance and AXIS Reinsurance.",
    'business_model': "AXIS Capital's business model centers on providing tailored risk management solutions while maintaining a disciplined underwriting approach. The company generates revenue through premiums collected from its insurance and reinsurance products, with a portion invested for additional income.",
    'moat_1': "Specialty Focus",
    'moat_2': "Underwriting Excellence",
    'moat_3': "Innovation and Technology Investment",
    'moat_4': "Diversified Portfolio and Global Reach",
    'peer_a': "WRB",
    'peer_b': "MKL",
    'peer_c': "CINF"
}

def update_axs_row():
    try:
        with open(large_missing_path, 'r') as f:
            lines = f.readlines()

        updated_lines = []
        found_axs_row = False
        for line in lines:
            if line.startswith('AXS,'):
                found_axs_row = True
                # Extract existing fields from the line
                fields = line.strip().split(',')
                
                # Construct the old string from the current line
                old_string = line

                # Update the relevant fields
                fields[7] = f'"' + axs_data['description'] + f'"'
                fields[8] = f'"' + axs_data['business_model'] + f'"'
                fields[9] = str(8060000000.000001) # market_cap_b is not in the original line, so we need to make sure it is not added
                fields[10] = axs_data['moat_1']
                fields[11] = axs_data['moat_2']
                fields[12] = axs_data['moat_3']
                fields[13] = axs_data['moat_4']
                fields[14] = axs_data['peer_a']
                fields[15] = axs_data['peer_b']
                fields[16] = axs_data['peer_c']

                # Construct the new string
                new_string = ','.join(fields) + '\r\n'
                
                # Use the replace tool
                print(default_api.replace(file_path=large_missing_path, old_string=old_string, new_string=new_string))
                
            updated_lines.append(line)

        if not found_axs_row:
            print("AXS row not found in the CSV.")

    except FileNotFoundError:
        print(f"Error: The file {large_missing_path} was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

update_axs_row()
