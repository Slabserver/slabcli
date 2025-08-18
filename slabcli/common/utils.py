import os


def file_has_extension(filename, extensions):
    """Return True if filename ends with one of the given extensions."""
    return filename.lower().endswith(tuple(ext.lower() for ext in extensions))

def file_newer_than(file, timestamp):
    """Return True if file was modified more recently than the provided timestamp."""

    try:
        mtime = os.path.getmtime(file)
    except OSError:
        return False
    if mtime > timestamp:
        return True
    return False

def substring_in_string(substrings, string):
    """Loop through a list of substrings to determine if any substring is found within a string"""

    substrings_to_check = substrings or []  # empty list to avoid errors
    for substring in substrings_to_check:
        if substring in string:
            return True
    return False
