BANNED_CHARS = [""" """, ".",  ",", "*", "+","-",":", "!", "?", "$", "@", "(", ")", "/", "\\", "'"]


def remove_spaces_from_string(s: str) -> str:
    safer_string = s
    for banned_char in BANNED_CHARS:
        safer_string = safer_string.replace(banned_char, "_")
    return safer_string


def is_long_enough(secs: int, min_length: int) -> bool:
    if secs == 0:
        return True
    return secs >= min_length * 60



def filter_length(episode: dict, min_length) -> bool:
    if is_long_enough(episode.get("duration", 0), min_length):
        return True
    return False
