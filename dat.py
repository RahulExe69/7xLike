import os
import json

def process_dat_files(directory):
    combined_data = []
    
    # Process each .dat file in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.dat'):
            filepath = os.path.join(directory, filename)
            
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    
                    # Extract UID and password
                    guest_info = data.get('guest_account_info', {})
                    combined_data.append({
                        "uid": guest_info.get('com.garena.msdk.guest_uid'),
                        "password": guest_info.get('com.garena.msdk.guest_password')
                    })
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                continue

    # Create output JSON file
    output_path = os.path.join(directory, 'combined_accounts.json')
    with open(output_path, 'w') as f:
        json.dump(combined_data, f, indent=4)
    
    print(f"Successfully combined {len(combined_data)} accounts into {output_path}")

if __name__ == '__main__':
    target_dir = input("Enter the directory path to process .dat files: ").strip()
    
    # Validate directory exists
    if not os.path.isdir(target_dir):
        print(f"Error: Directory '{target_dir}' does not exist!")
        exit(1)
        
    process_dat_files(target_dir)