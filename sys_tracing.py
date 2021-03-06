__author__ = 'Aknox'
"""
    add the @allow_tracking decorator to a webbapp2.RequestHandler
    to track all functions called when trying to access the url it handles
"""

from collections import OrderedDict
import time

# Settings Defaults
_SHOW_DETAILED_CALL_ORDER = True
_SHOW_TIMING = True
_SHOW_RESPONSES = True
_PATHS_TO_SPLIT = frozenset(['path-analyzer'])
_PATHS_TO_IGNORE = frozenset(['/Frameworks/Python.framework', '/Resources/google_appengine/'])


class FunctionStats(object):
    def __init__(self, name):
        self.function_name = name
        self.times_called = 0
        self.cumulative_operation_time = 0
        self.responses = []


def tracker(frame, event, arg, func_stack=[], func_timing_stack=[], function_stats=OrderedDict(), counters=[0, 0]):

    # Setup frame info
    co = frame.f_code
    func_filename = co.co_filename
    func_name = co.co_name

    # Ignore calls to files in certain locations
    try:
        for path in _PATHS_TO_IGNORE:
            if path in func_filename:
                return tracker
    except TypeError:
        pass

    # Remove unnecessary path info to make logs more readable
    try:
        for path in _PATHS_TO_SPLIT:
            func_filename = func_filename.split(path)
            func_filename = func_filename[len(func_filename)-1]
    except TypeError:
        pass

    # Add the class to the function name if one could be found
    try:
        self_argument = frame.f_code.co_varnames[0]  # This *should* be 'self'.
        instance = frame.f_locals[self_argument]
        class_name = instance.__class__.__name__
        func_name = class_name + '.' + func_name
    except IndexError:
        pass

    function_full_name = func_filename + ' ln:' + str(frame.f_lineno) + ' - ' + func_name

    if event == 'call':
        if "internal_tracking_wrapper" in function_full_name and _SHOW_TIMING:
            print "\n\rFunction Call Order"

        if function_full_name not in function_stats:
            try:
                function_stats[function_full_name] = FunctionStats(function_full_name)
            except TypeError:
                pass

        func_stack.append(function_full_name)
        try:
            func_timing_stack.append((function_full_name, time.clock()))
        except AttributeError:
            pass

        # Reset extension counter to current depth if getting deeper again
        if counters[1] == -1:
            counters[1] = counters[0]
        counters[0] += 1  # Current Depth
        counters[1] += 1  # -1 or Current depth if getting deeper

    elif event == "return":
        if counters[0] == counters[1]:
            if _SHOW_DETAILED_CALL_ORDER:
                print func_stack
            counters[1] = -1

            # Replace any paths with dashes to make new calls more obvious
            for row in range(0, len(func_stack)-1):
                func_stack[row] = '-' * (len(func_stack[row]) + func_stack[row].count('\\'))
        counters[0] -= 1

        func_stack.pop()
        function_full_name, start_time = func_timing_stack.pop()

        function_stats[function_full_name].times_called += 1
        function_stats[function_full_name].cumulative_operation_time += time.clock() - start_time
        function_stats[function_full_name].responses.append(arg)

        if "internal_tracking_wrapper" in function_full_name:
            if _SHOW_TIMING:
                print "\n\rFunction Call Timing And Order Summary"
                print "Call Order\tCall Count\tCum. Run Time\tAvg. Run Time\tFunction Called\tResponses"
                i = 0
                for name, f_stats in function_stats.items():
                    i += 1
                    print i, '\t\t\t', f_stats.times_called, '\t\t\t', f_stats.cumulative_operation_time, '\t\t', f_stats.cumulative_operation_time/f_stats.times_called, '\t\t', name

            if _SHOW_RESPONSES:
                print "\n\rFunction Responses"
                print "Function Called\tResponses By Call Order From Oldest To Newest"
                for name, f_stats in function_stats.items():
                    print name, '\t\t',  f_stats.responses

    return tracker


def allow_tracking(func):
    import sys
    sys.settrace(tracker)

    def internal_tracking_wrapper(*args, **kwargs):
        operation_response = func(*args, **kwargs)
        return operation_response

    return internal_tracking_wrapper