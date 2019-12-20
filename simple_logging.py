# TODO: I plan on migrating this sometime later to make it compatible with the python logging library
# If anyone wants to help me with that, please do contact me

import time
import sys
import os
import re
from io import StringIO
from collections import namedtuple

import colorama
from colorama import Fore, Back, Style, AnsiToWin32

colorama.init(wrap=False)

Message = namedtuple('Message', ['type', 'time', 'text'])

SYMBOL = {
    'error': 'X',
    'warn': '!',
    'success': '*',
    'info': '-',
    'unknown': '?',
    'debug': '#'
}

SYMBOL_TO_TYPE = {SYMBOL[type]: type for type in SYMBOL}

LEVEL = {
    'error': 4,
    'warn': 3,
    'success': 2,
    'info': 1,
    'unknown': 1,
    'debug': 0
}


class Logger:
    # This may be changed
    TEXT_COLOR = {
        'error': Fore.RED,
        'warn': Fore.MAGENTA,
        'success': Fore.GREEN,
        'info': Fore.CYAN,
        'unknown': Fore.WHITE,
        'debug': Fore.YELLOW
    }

    # INTERNAL STATIC FUNCTIONS
    @staticmethod
    def time_stamp():
        """[Internal] Gives a timestamp, along with the time, for the current time in YYYY-MM-DD hh:mm:ss format."""
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time()))
        t = time.strptime(ts, "%Y-%m-%d %H:%M:%S")
        return ts, t

    @staticmethod
    def curdate():
        """[Internal] Gives a timestamp for the current date in YYYY_MM_DD format."""
        return time.strftime("%Y_%m_%d", time.gmtime(time.time()))

    # You can override this if nescessary
    @staticmethod
    def get_type(type):
        """[Internal] Converts various aliases to the correct message type.

        ERROR   = X, e, err, error, error_message
        WARN    = !, w, warn, warning, warning_message
        SUCCESS = *, s, success, success_message
        INFO    = -, i, info, info_message
        DEBUG   = #, d, debug, debug_message
        UNKNOWN = everything else
        """
        type = str(type).lower()
        if type in ['X', 'e', 'err', 'error', 'error_message']:
            return 'error'
        if type in ['!', 'w', 'warn', 'warning', 'warning_message']:
            return 'warn'
        if type in ['*', 's', 'success', 'success_message']:
            return 'success'
        if type in ['-', 'i', 'info', 'info_message']:
            return 'info'
        if type in ['#', 'd', 'debug', 'debug_message']:
            return 'debug'

        return 'unknown'

    @classmethod
    def important(cls, type, level):
        return LEVEL[type] >= level

    # Constructor

    def __init__(self, name, log_folder=None, log_level='info', output_level='success', out_stream=sys.stdout, output_to_stderr=False):
        """Initialize the logger."""
        self.name = name
        self.colored_out = AnsiToWin32(out_stream).stream
        t = self.get_type(log_level)
        if t != 'unknown':
            self.log_level = LEVEL[t]
        else:
            # type() or isinstance()?
            # ig type() is better here
            if type(log_level) == int:
                self.log_level = log_level  # discouraged
            elif str(log_level).lower() == 'none':
                self.log_level = 5
            else:
                self.log_level = 1
        t = self.get_type(output_level)
        if t != 'unknown':
            self.output_level = LEVEL[t]
        else:
            if type(output_level) == int:
                self.output_level = output_level  # discouraged
            elif str(output_level).lower() == 'none':
                self.output_level = 5
            else:
                self.output_level = 2
        self.output_to_stderr = output_to_stderr
        self.log_folder = None
        if log_folder != None:
            self.log_folder = log_folder
            if(not os.path.isdir(log_folder)):
                os.makedirs(log_folder)
            self.make_logs()

    def make_logs(self):
        """[Internal] Generate names for log files by date."""
        self.log_file = os.path.join(self.log_folder, self.name + "-" + self.curdate() + ".log")
        self.log_meta = os.path.join(
            self.log_folder, self.name + "-" + self.curdate() + ".log.meta")

    def message(self, type, *args, force_print=False, force_log=False, **kwargs):
        """Prints a (colorized) message, logging it to a file if nescessary.

        <type> is either ERROR, WARN, SUCCESS, INFO, or DEBUG, or their aliases
        ERROR   = X, e, err, error, error_message
        WARN    = !, w, warn, warning, warning_message
        SUCCESS = *, s, success, success_message
        INFO    = -, i, info, info_message
        DEBUG   = #, d, debug, debug_message

        If <force_print> or <force_log> are True, a message is always printed or always logged (respectively).

        Note that if printing to stderr is enabled, all error messages are printed (to stderr) irrespective of other settings

        <args> and <kwargs> are passed directly to print().
        """
        type = self.get_type(type)
        ts, t = self.time_stamp()
        if force_print or self.important(type, self.output_level):
            print(self.TEXT_COLOR[type], '[', SYMBOL[type], ' @ ',
                  ts, ']', file=self.colored_out, sep='', end='')
            print(*args, file=self.colored_out, **kwargs)
            print(Style.RESET_ALL, file=self.colored_out, end='')
        if self.output_to_stderr and type == 'error':
            print(*args, file=sys.stderr, **kwargs)
        if self.log_folder != None and (self.important(type, self.log_level) or force_log):
            pos1 = -1
            pos2 = -1
            with open(self.log_file, 'a+') as log:
                print('[', SYMBOL[type], ' @ ', ts, ']',
                      file=log, sep='', end='')
                pos1 = log.tell()
                print(*args, file=log, **kwargs, flush=True)
                pos2 = log.tell()
            with open(self.log_meta, 'a+') as meta:
                print('[', SYMBOL[type], ' @ ', ts, ']', str(pos1), ':', str(pos2),
                      file=meta, sep='')
        msg = None
        with StringIO() as str_buf:
            print(*args, file=str_buf, **kwargs)
            msg = str_buf.getvalue()
        return Message(type, t, msg)

    # WRAPPER FUNCTIONS
    # Not the most useful things

    def error(self, *args, **kwargs):
        return self.message('error', *args, **kwargs)

    def warn(self, *args, **kwargs):
        return self.message('warn', *args, **kwargs)

    def success(self, *args, **kwargs):
        return self.message('success', *args, **kwargs)

    def info(self, *args, **kwargs):
        return self.message('info', *args, **kwargs)

    def debug(self, *args, **kwargs):
        return self.message('debug', *args, **kwargs)


class LogReader:
    """Read logs."""
    FORMAT = r"\[(?P<type>[X!*\-?#]) @ (?P<time>%Y-%m-%d \d\d:\d\d:\d\d)\](?P<begin>-?\d+):(?P<end>-?\d+)"
    default_log = Logger('default_log')
    def __init__(self, log_folder, name, log=None):
        self.log_folder = log_folder
        self.name = name
        if log == None:
            self.log = self.default_log
        else:
            self.log = log
        self.messages = {}

    def load_date(self, date):
        format = time.strftime(self.FORMAT, date)
        f_name = time.strftime("%Y_%m_%d", date)

        log_file = os.path.join(self.log_folder, self.name + f_name + ".log")
        meta_file = os.path.join(self.log_folder, self.name + f_name + ".log.meta")

        self.messages[date] = []

        with open(meta_file, 'r') as meta, open(log_file, 'r') as log:
            for i, line in enumerate(meta):
                prop = re.search(format, line)
                if prop == None:
                    self.log.warn_message("Incorrect format on line {} of {}: {}".format(i+1, f_name + ".log.meta", line))
                    continue
                begin, end = int(prop.group('begin')), int(prop.group('end'))
                log.seek(begin)
                text = log.read(end - begin - 1)
                type = prop.group('type')
                msg_time = time.strptime(
                    prop.group('time'), "%Y-%m-%d %H:%M:%S")
                self.messages[date] += [Message(type, msg_time, text)]

        return self.messages[date]

    def load_all(self):
        for file in os.listdir(self.log_folder):
            if file.startswith(self.name) and file.endswith(".log.meta"):
                self.log.debug_message("File found: ", file)
                self.load_date(time.strptime(file, self.name+"%Y_%m_%d.log.meta"))
        return self.messages
