def has_file_extension(filename, file_extensions):
    """Return True if filename ends with one of the given extensions."""
    return filename.lower().endswith(tuple(ext.lower() for ext in file_extensions))

def is_substring_in_string(substrings, path):
    """Loop through a list of substrings to determine if any substring is found within a directory path"""

    substrings_to_check = substrings or []  # empty list to avoid errors
    for substring in substrings_to_check:
        if substring in path:
            return True
    return False