```py
def flatten(arr):
    result = []
    for x in arr:
        if isinstance(x, list):
            result.extend(flatten(x))
        else:
            result.append(x)
    return result
```