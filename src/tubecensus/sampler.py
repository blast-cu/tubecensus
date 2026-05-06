import os
import random

def sample_one(path):
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        f.seek(random.randint(0, size - 1))
        f.readline()  # discard partial line
        line = f.readline().decode(errors="replace")
        if not line:
            return None
    return line.rstrip('\n')

def sample_many(path,n):
    lines=[]
    size = os.path.getsize(path)
    with open(path, "rb") as f:
        count = 0
        while count < n:
            f.seek(random.randint(0, size - 1))
            f.readline()  # discard partial line
            line = f.readline().decode(errors="replace")
            if not line:
                continue
            lines.append(line.rstrip('\n'))
            count += 1
    return lines
