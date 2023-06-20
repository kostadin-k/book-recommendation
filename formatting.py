def secondary(out):
    return f"\033[37m\033[3m{out}\033[0m"

def title(out):
    return f"\033[1m{out}\033[0m"

def accent(out):
    return f"\033[36m{out}\033[0m"

def error(out):
    return f"\033[31m{out}\033[0m"

def fatal_error(out):
    return f"\033[31m\033[1m{out}\033[0m"