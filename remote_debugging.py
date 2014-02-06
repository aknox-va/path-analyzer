__author__ = 'Aknox'
"""
Add the decorator @allow_remote_debugging to any functions you would like to be able to debug remotely.
This decorator should not be added to class definitions or class methods.

Run something like the following in interactive console to enable debugging for
all functions with the decorator @allow_remote_debugging. By default debugging will be enabled for 1 hour.
To change that time add the keyword 'expiry_date' with the value being the number of seconds to enable debugging.

from remote_debugger import enable_debugging
enable_debugging(
    {
        'get_account': [
            (13, 4),
            (17, 4)
            ],
        'entity_to_obj': None
    },
    False
)

If avoid is set to True then any keys listed in the special_functions dictionary that match a function name in the
program will not have debugging enabled. Everything else will.

If avoid is set to False then only the functions in special_functions will have debugging enabled. The function's
local variables may be printed at any time by adding a list of tuples to the dictionary key. The dictionary values
should be None if no print statements are needed and in the below form if they are:
[(<line to insert a fence below>,<number of spaces to indent the statement>), ...]

Set avoid=True and special_functions={}

To stop debugging from happening run the following:
from remote_debugger import disable_debugging
disable_debugging()
"""
import logging
import inspect
from functools import wraps
from google.appengine.api import memcache
from types import FunctionType

DEBUG_FUNCTIONS_LIST_KEY = "remoteDebuggerFunctions"


# check a memcache entry to see if debug is enabled
# allow a url param to enable/disable debug and possibly specify a specific function to debug
DEBUG_ENABLED = True


#display output to a custom window? chrome extension?
def allow_remote_debugging(func):
    # Don't wrap in the debug function if global debugging is disabled
    if not DEBUG_ENABLED:
        return func

    # Only debug if this functions has been chose for debugging
    settings = memcache.get(key=DEBUG_FUNCTIONS_LIST_KEY)

    if not (isinstance(settings, dict)
            and isinstance(settings.get('avoid'), bool)
            and isinstance(settings.get('special_functions'), dict)):
        return func

    @wraps(func)
    def monitor(*args, **kwargs):
        # Check a memcache entry for a specific function to enable debugging info for. If there is one then
        # only show monitor data if this is one of them
        if not (isinstance(settings, dict)
                and isinstance(settings.get('avoid'), bool)
                and isinstance(settings.get('special_functions'), dict)):
            return func(*args, **kwargs)

        # Check a memcache entry for a specific function to enable debugging info for. If there is one then then
        # only show monitor data if this is that function
        if settings['avoid']:
            if func.func_name in settings['special_functions']:
                return func(*args, **kwargs)
        else:
            if func.func_name not in settings['special_functions']:
                return func(*args, **kwargs)

        logging.info("RD-CALLING: {1}(args={2}, kwargs={3})".format(func.func_name, args, kwargs))

        # get the function code
        code = inspect.getsourcelines(func)[0]

        # build the expected function definition
        func_def = "def {0}".format(func.func_name)

        # insert local variable print statements on requested lines
        fences = settings.get('special_functions', {}).get(func.func_name)

        if fences:
            fences.sort(key=lambda x: x[0], reverse=True)
            for line_number, indent in fences:
                if line_number < len(code):
                    code.insert(line_number, " "*indent + "logging.info( \'RD-FENCE LN{0}: {{0}}\'.format(locals()))\r".format(line_number))
                else:
                    logging.error("couldn't add fence because the line number {0} is out of bounds".format(line_number))

            # remove the allow monitoring decorator and change the function definition name
            # to keep from messing with any existing functions
            for line in code[:]:
                if "@allow_remote_debugging" in line:
                    code.remove(line)

                if func_def in line:
                    start = line.index(func_def)
                    end = start + len(func_def)
                    code[code.index(line)] = line[0:start] + "def debugging_{0}".format(func.func_name) + line[end:]
                    break

            # add a line to run the function in the proper context
            code.append("debug_response = debugging_{0}(*{1}, **{2})".format(func.func_name, args, kwargs))

            # define and run the function
            exec """""".join(code) in func.func_globals
            # return the response to the calling function
            response = func.func_globals['debug_response']
        else:
            # Just run the function without modifying it
            response = func(*args, **kwargs)

        # Display the function's response
        logging.info("RD-RESPONSE: '{0}' returned '{1}'\n".format(func.func_name, response))

        # pass the response back to the calling function
        return response

    return monitor


def decorate_all(decorator):
    def deco_decorate(klass):
        for attr, attrval in klass.__dict__.items():
            if type(attrval) is FunctionType:
                setattr(klass, attr, decorator(attrval))        # Not __dict__
        return klass
    return deco_decorate


def enable_debugging(special_functions, avoid, expiry_date=3600):
    #todo: will probably have to worry about functions in different objects or modules that have the same name
    """
    Enables debugging for specific functions
    :param special_functions: a dictionary of the names of functions that debug should not run on with a list of
                              tuples [(<line to insert a fence below>,<number of spaces to indent the statement>), ...].
                              set the dictionary item value to None if avoid is true or not adding fences for the func.
    :param avoid: if true then all functions except the special_functions will have debug enabled
                  if false then only special_functions will be run.
    :param expiry_date: how long debugging will be enabled. the default is 1 hour
    """
    # anything but a list with more than one value should enable debugging for everything
    if not isinstance(special_functions, dict):
        raise ValueError(
            "special_functions must be a dictionary. "
            "Enter an empty dictionary with avoid set to True to enable debugging for all functions"
        )
    if not isinstance(avoid, bool):
        raise ValueError(
            "the avoid param must be a boolean. 'False' will cause only special_functions to have debugging enabled. "
            "'True' will cause all but the special_functions to have debugging enabled."
        )
    memcache_entry = {'avoid': avoid, 'special_functions': special_functions}
    memcache.set(key=DEBUG_FUNCTIONS_LIST_KEY, value=memcache_entry, time=expiry_date)


def disable_debugging():
    memcache.delete(key=DEBUG_FUNCTIONS_LIST_KEY)
