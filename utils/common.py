BANNED_CHARS = [""" """, ".",  ",", "*", ":", "!", "?", "$", "@", "(", ")", "/", "\\", "'"]


def remove_spaces_from_string(s: str) -> str:
    safer_string = s
    for banned_char in BANNED_CHARS:
        safer_string = safer_string.replace(banned_char, "_")
    return safer_string
