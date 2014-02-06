__author__ = 'Aknox'
"""
    add the following code to a webbapp2.RequestHandler to track all functions called when trying to access the url it handles
    import sys
    from path-anayzer.sys_tracing import tracker
    sys.settrace(tracker)
"""

def tracker(frame, event, arg, func_stack=[], counters=[0, 0]):
    paths_to_ignore = ['/Frameworks/Python.framework', '/Resources/google_appengine/']
    paths_to_split = []

    co = frame.f_code
    func_filename = co.co_filename
    func_name = co.co_name

    # Ignore calls to files in certain locations
    for path in paths_to_ignore:
        if path in func_filename:
            return tracker

    # Remove unecessary path info to make logs more readable
    for path in paths_to_split:
        func_filename = func_filename.split(path)
        func_filename = func_filename[len(func_filename)-1]

    if event == 'call':
        try:
            self_argument = frame.f_code.co_varnames[0]  # This *should* be 'self'.
            instance = frame.f_locals[self_argument]
            class_name = instance.__class__.__name__
            func_name = class_name + '.' + func_name
        except Exception:
            pass

        func_stack.append(func_filename + ' : ' + func_name + '(' + str(frame.f_lineno) + ')')
        # Reset extension counter to current depth if getting deeper again
        if counters[1] == -1:
            counters[1] = counters[0]
        counters[0] += 1  # Current Depth
        counters[1] += 1  # -1 or Current depth if getting deeper

    elif event == "return":
        if counters[0] == counters[1]:
            print func_stack
            counters[1] = -1

            # Replace any paths with dashes to make new calls more obvious
            for row in range(0, len(func_stack)-1):
                func_stack[row] = '-' * (len(func_stack[row]) + func_stack[row].count('\\'))
        counters[0] -= 1

        func_stack.pop()

    return tracker