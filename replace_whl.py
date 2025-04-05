import os

def replace_in_filenames(directory):
    for filename in os.listdir(directory):
        if 'linux_x86_64.whl' in filename:
            new_filename = filename.replace('linux_x86_64.whl', 'manylinux1_x86_64.whl')
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
        # 13 is x86_64, 14 is arm64
        if 'macosx_13_0_universal2.whl' in filename:
            new_filename = filename.replace('macosx_13_0_universal2.whl', 'macosx_13_0_x86_64.whl')
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
        if 'macosx_14_0_universal2.whl' in filename:
            new_filename = filename.replace('macosx_14_0_universal2.whl', 'macosx_14_0_arm64.whl')
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_filename))
# Replace './' with the actual directory path if needed
replace_in_filenames('dist')