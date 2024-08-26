import os

def replace_in_filenames(directory):
    for filename in os.listdir(directory):
        if 'linux_x86_64.whl' in filename:
            new_filename = filename.replace('linux_x86_64.whl', 'manylinux1_x86_64.whl')
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))

# Replace './' with the actual directory path if needed
replace_in_filenames('dist')