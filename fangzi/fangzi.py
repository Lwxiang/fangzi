# -*- coding: utf-8 -*-
import pymongo
import optparse
from settings import *


class FangZi(object):
    """

    """

    finder = {
        'IMPORT': ['@IMPORT_BEGIN@', '@IMPORT_END@'],
        'STATIC': ['@STATIC_BEGIN@', '@STATIC_END@'],
        'FUNC': ['@FUNC_BEGIN@', '@FUNC_END@',
                 '@FUNC_HEAD_BEGIN@', '@FUNC_HEAD_END@',
                 '@FUNC_CODE_BEGIN@', '@FUNC_CODE_END@',
                 '@FUNC_SPLIT@'],
        }

    def __init__(self, url=URL, port=PORT, database=DATABASE, collection=COLLECTION):

        conn = pymongo.Connection(url, port)
        db = conn[database]
        self.posts = db[collection]
        self.import_collector = ''
        self.static_collector = ''
        self.func_collector = []

    def status(self):
        """
            List the status of database
            ---------------------------------------
             FunctionName   Flag    Group   Status
            ---------------------------------------
             IMPORT_PART    IMPORT  Default Working
             STATIC_PART    STATIC  Default Working
             Check_Time     CODE    Tourist Off
             Check_Name     CODE    VIP     Working
            ---------------------------------------
            Function name is the name of those functions we submit to database
            Flag is the type of the function/data, such as IMPORT statements or CODE part(function part)
            Group is the second-level flag, for example, some check code is for tourist-request while some is for VIP
            Status is a mark that if this function is going to be used, just like a switch
        """

        print
        checkers = self.posts.find({})
        print "%-30s %-20s %-20s %s" % ('FunctionName', 'Flag', 'Group', 'Status')
        print '-' * 80
        for checker in checkers:
            print "%-30s %-20s %-20s %s" % (
                checker['_id'][:25] if len(str(checker['_id'])) > 25 else checker['_id'],
                checker['flag'],
                checker['group'],
                'Working' if checker['switch'] else 'Off'
                )
        print

    def wake(self, checkers, opt):

        if opt.all:
            self.posts.update({}, {"$set": {"switch": True}}, multi=True)
            return True, ''

        if opt.flag:
            if not self.posts.find_one({"flag": opt.flag}):
                    return False, 'Flag %s' % opt.flag
            self.posts.update({"flag": opt.flag}, {"$set": {"switch": True}}, multi=True)

        elif opt.group:
            if not self.posts.find_one({"group": opt.group}):
                    return False, 'Group %s' % opt.group
            self.posts.update({"group": opt.group}, {"$set": {"switch": True}}, multi=True)

        else:
            for checker in checkers:
                if not self.posts.find_one({'_id': checker}):
                    return False, checker

            for checker in checkers:
                self.posts.update({"_id": checker}, {"$set": {"switch": True}})

        return True, ''

    def close(self, checkers, opt):

        if opt.all:
            self.posts.update({}, {"$set": {"switch": False}}, multi=True)
            return True, ''

        if opt.flag:
            if not self.posts.find_one({"flag": opt.flag}):
                    return False, 'Flag %s' % opt.flag
            self.posts.update({"flag": opt.flag}, {"$set": {"switch": False}}, multi=True)

        elif opt.group:
            if not self.posts.find_one({"group": opt.group}):
                    return False, 'Group %s' % opt.group
            self.posts.update({"group": opt.group}, {"$set": {"switch": False}}, multi=True)

        else:
            for checker in checkers:
                if not self.posts.find_one({'_id': checker}):
                    return False, checker

            for checker in checkers:
                self.posts.update({"_id": checker}, {"$set": {"switch": False}})

        return True, ''

    def remove(self, checkers, opt):

        if opt.all:
            self.posts.remove()
            return True, ''

        if opt.flag:
            if not self.posts.find_one({"flag": opt.flag}):
                    return False, 'Flag %s' % opt.flag
            self.posts.remove({'flag': opt.flag})

        elif opt.group:
            if not self.posts.find_one({"group": opt.group}):
                    return False, 'Group %s' % opt.group
            self.posts.remove({'group': opt.group})

        else:

            for checker in checkers:
                if not self.posts.find_one({"_id": checker}):
                    return False, checker

            for checker in checkers:
                self.posts.remove({'_id': checker})

        return True, ''

    def parse(self, lines):
        """
            Parse the source code from the file where your functions is
            and split them into 4 part:
                1.import part:
                    A String
                    all import in the file,
                    import statements in functions.py(or other source file)
                    import statements in checker.py(or other process file)
                    notice that the sys-path of them should be same
                    +---------------
                        +your_project_dir
                            -functions.py
                            -checker.py
                        +other dir
                    +---------------
                    or some ImportError may occurs
                2.static part:
                    A String
                    all static statements in the file,
                    includes the class and other no-def pre-work
                3.function part:
                    A List
                    all functions in the file,
                    it is the main part of the project
                4.note part:
                    No Stored
                    all notes in the file,
                    include # and "*3
                    but it will not be stored
        """

        def note_cleaner(now_lines):

            now_step = 0
            while now_step + 1 <= len(now_lines):
                now_line = now_lines[now_step].replace(' ', '')
                if now_line and now_line[0] == '#':
                    del now_lines[now_step]
                else:
                    now_step += 1

            now_step = 0

            while now_step + 1 <= len(now_lines):
                now_line = now_lines[now_step].replace(' ', '')
                if now_line.find("\"\"\"") > -1:
                    del now_lines[now_step]
                    while now_lines[now_step].find("\"\"\"") == -1:
                        del now_lines[now_step]
                    del now_lines[now_step]
                else:
                    now_step += 1

            return now_lines

        def go_next(now_step):
            if now_step + 1 >= len(lines):
                return now_step, False
            now_step += 1
            return now_step, True

        # Parse by step, step is the line in source file
        step = 0

        # Initialize the collector
        # import and static part collect all the content by a single string, split line with "\n"
        # function part collect functions by a list, one function in one cell:
        #   list = [
        #       ...
        #       [
        #           function_source_code,
        #           function_name,
        #           function_parameters,
        #       ],
        #       ...
        #   ]
        import_collector = ''
        static_collector = ''
        func_collector = []

        # Clean the NOTES in source file
        lines = note_cleaner(lines)

        # Process by step
        # lines: the source file split into lines
        while step + 1 <= len(lines):

            # Get step line, remove the \n and \r, so we can process with a pure line
            line = lines[step].replace('\n', '').replace('\r', '')

            # If it is a blank line, go next line
            if not line:
                step += 1
                continue

            # Find import, such as "import time" or "from time import time"
            if line.find("import ") != -1:
                while True:
                    import_collector += line if not import_collector else '\n' + line

                    # Process the multi-line import situation:
                    # from settings import URL, TOKEN \
                    #                      SECRET_KEY, ID_KEY
                    # Take them all in
                    if line.find("\\") == -1 or step + 1 >= len(lines):
                        break

                    # Go to next line
                    step, flag = go_next(step)

                    # If out of file then break
                    if not flag:
                        break
                    line = lines[step].replace('\n', '').replace('\r', '')

            # Find def, append it to func_collector
            elif line.find("def ") == 0:
                # No continuation exists before function-head
                line_continuation = False

                # Initialize collector, it is one cell in func_collector list
                collector = ''

                # get function name and parameters
                def_name = line[line.index("def")+3:line.index("(")].replace(' ', '')
                def_para = line[line.index("(")+1:line.index(")")].replace(' ', '')

                # Mark the first line as the function-head
                first_def = True
                while True:

                    # If it is a blank line, check if it is out of file then go next line
                    if not line.replace(' ', ''):

                        # Go to next line
                        step, flag = go_next(step)

                        # If out of file then break
                        if not flag:
                            break
                        line = lines[step].replace('\n', '').replace('\r', '')
                        continue

                    # The indent of this line is 0,
                    # and it is not the function-head,
                    # and there is not a continuation in the last line
                    # then we consider this line is out of function(may be a import or static statement)
                    # so that step go back one line, and jump out the def-processor
                    if line.find(' ') > 0 and not first_def and not line_continuation:
                        step -= 1
                        break

                    # Cancel the function-head mark
                    first_def = False

                    # Check if there is a continuation "\" in the tail
                    line_continuation = line.find('\\') != -1

                    # Add the line as one line of this function
                    collector += line if not collector else '\n' + line

                    # Go to the next line
                    step, flag = go_next(step)

                    # If out of file then break
                    if not flag:
                        break
                    line = lines[step].replace('\n', '').replace('\r', '')

                # After process, one function is done and will be append to func_collector
                # contains: [source_code, name, parameters]
                func_collector.append([collector + '\n', def_name, def_para])

            # The left is static part
            else:
                while True:

                    # If it is a blank line then break
                    if not line.replace(' ', ''):
                        break

                    # If import or def occur, then we consider this line is out of static statement
                    if line.find("import ") != -1 or line.find("def ") == 0:
                        break

                    static_collector += line if not static_collector else '\n' + line

                    # Go to the next line
                    step, flag = go_next(step)

                    # If out of file then break
                    if not flag:
                        break
                    line = lines[step].replace('\n', '').replace('\r', '')

            # One is handled then do next since next line
            step += 1

        # Store in class attributes
        self.import_collector = import_collector + '\n'
        self.static_collector = static_collector + '\n'
        self.func_collector = func_collector

    def hull(self):
        try:
            for index in range(0, len(self.func_collector)):
                self.func_collector[index][0] = self.huller(self.func_collector[index][0])
        except Exception, e:
            return False, e

        return True, ''

    @staticmethod
    def huller(string):
        string = string.replace('\n    ', '\n')[string.find('\n')+1:]
        pos_start = 0
        while string.find('return ', pos_start) != -1:
            pos = string.find('\n', string.find('return ', pos_start))
            string = "%s;raise Exception(%s)%s" % (string[:pos], CATCHER, string[pos:])
            pos_start = pos + 1
        string = string.replace('return', '%s =' % CATCHER)
        return string

    def parse_from_file(self, file_path=FILE_PATH):
        try:
            source_code = open(file_path, 'r')
        except Exception, e:
            return False, e

        lines = source_code.readlines()

        self.parse(lines)

        # try:
        #     self.parse(lines)
        # except Exception, e:
        #     return False, e

        return True, ''

    def parse_from_string(self, string=''):
        lines = string.split('\n')

        try:
            self.parse(lines)
        except Exception, e:
            return False, e

        return True, ''

    def save_parse(self):
        try:
            f = open('parse_temp', 'w')
        except Exception, e:
            return False, e

        f.write('%s\n' % self.finder['IMPORT'][0])
        f.write(self.import_collector)
        f.write('%s\n' % self.finder['IMPORT'][1])

        f.write('%s\n' % self.finder['STATIC'][0])
        f.write(self.static_collector)
        f.write('%s\n' % self.finder['STATIC'][1])

        f.write('%s\n' % self.finder['FUNC'][0])
        first = True
        for func in self.func_collector:
            f.write('' if first else '%s\n' % self.finder['FUNC'][6])
            first = False

            f.write('%s\n' % self.finder['FUNC'][2])
            f.write('%s(%s)\n' % (func[1], func[2]))
            f.write('%s\n' % self.finder['FUNC'][3])
            f.write('%s\n' % self.finder['FUNC'][4])
            f.write(func[0])
            f.write('%s\n' % self.finder['FUNC'][5])
        f.write('%s\n' % self.finder['FUNC'][1])
        f.close()

        return True, ''

    def load_parse(self):

        f = open('parse_temp', 'r')
        raw_string = f.read()

        try:
            import_begin = raw_string.find(self.finder['IMPORT'][0])
            import_end = raw_string.find(self.finder['IMPORT'][1])

            if (import_begin == -1) ^ (import_end == -1):
                raise Exception('Load Failed')

            static_begin = raw_string.find(self.finder['STATIC'][0])
            static_end = raw_string.find(self.finder['STATIC'][1])

            if (static_begin == -1) ^ (static_end == -1):
                raise Exception('Load Failed')

            func_begin = raw_string.find(self.finder['FUNC'][0])
            func_end = raw_string.find(self.finder['FUNC'][1])

            if (func_begin == -1) ^ (func_end == -1):
                raise Exception('Load Failed')

            if import_begin != -1:
                import_collector = raw_string[import_begin + len(self.finder['IMPORT'][0]): import_end]
            else:
                import_collector = ''

            if static_begin != -1:
                static_collector = raw_string[static_begin + len(self.finder['STATIC'][0]): static_end]
            else:
                static_collector = ''

            func_collector = []
            if func_begin != -1:
                funcs = raw_string[func_begin + len(self.finder['FUNC'][0]): func_end].split(self.finder['FUNC'][6])

                for func in funcs:
                    func_head_begin = func.find(self.finder['FUNC'][2])
                    func_head_end = func.find(self.finder['FUNC'][3])
                    func_code_begin = func.find(self.finder['FUNC'][4])
                    func_code_end = func.find(self.finder['FUNC'][5])
                    if func_head_begin == -1 or func_head_end == -1 or \
                       func_code_begin == -1 or func_code_end == -1:
                        raise Exception('Load Failed')

                    func_head = func[func_head_begin + len(self.finder['FUNC'][2]): func_head_end]
                    func_head = func_head.replace('\n', '').replace('\r', '').replace('\t', '')
                    func_name = func_head[:func_head.index("(")].replace(' ', '')
                    func_para = func_head[func_head.index("(")+1: func_head.index(")")].replace(' ', '')
                    func_code = func[func_code_begin + len(self.finder['FUNC'][4]): func_code_end]

                    func_collector.append([func_code, func_name, func_para])

            self.import_collector = import_collector
            self.static_collector = static_collector
            self.func_collector = func_collector

            return True, ''

        except Exception, e:
            return False, e

    def submit(self, body, id_name, flag='Undefined', group='Undefined', switch=False, cover=False, **kwargs):

        if cover:
            self.posts.remove({"_id": id_name})

        self.posts.insert({"_id": id_name})

        data = dict({"flag": flag,
                     "group": group,
                     "switch": switch,
                     "body": body}.items() + kwargs.items()
                    )
        self.posts.update({"_id": id_name}, {"$set": data})

    def launch(self):
        try:
            if IMPORT_POST:
                self.submit(body=self.import_collector, id_name='IMPORT_PART', flag='IMPORT')
            if STATIC_POST:
                self.submit(body=self.static_collector, id_name='STATIC_PART', flag='STATIC')
            if FUNC_POST:
                for collector in self.func_collector:
                    self.submit(body=collector[0], id_name=collector[1], flag='CODE', para=collector[2])
        except Exception, e:
            return False, e

        return True, ''


def main():
    poster = FangZi()

    p = optparse.OptionParser()
    p.add_option('--status', '-s', action='store_true', default=False, help='Show the status of stored functions')
    p.add_option('--wake', '-w', action='store_true', default=False, help='Turn on the funcs f1, f2, .. or all')
    p.add_option('--close', '-c', action='store_true', default=False, help='Turn off the funcs f1, f2, .. or all')
    p.add_option('--parse', '-p', action='store_true', default=False, help='Parse and Hull')
    p.add_option('--launch', '-l', action='store_true', default=False, help='Launch the post')
    p.add_option('--remove', '-r', action='store_true', default=False, help='Remove the funcs f1, f2, .. or all')
    p.add_option('--all', '-a', action='store_true', default=False, help='Wake/Close/Remove All')
    p.add_option('--flag', '-f', action='store', default='', help='Wake or Close by Flag f')
    p.add_option('--group', '-g', action='store', default='', help='Wake or Close by Group g')

    options, arguments = p.parse_args()

    if options.remove:
        success, error = poster.remove(arguments, options)
        print 'Remove actions is OK' if success else 'Remove Failed: \'%s\' Does Not Exist' % error

    if options.parse:
        success, error = poster.parse_from_file()
        print 'Parse actions is OK' if success else 'Parse Failed: %s' % error

        if success:
            success, error = poster.hull()
            print 'Hull actions is OK' if success else 'Hull Failed: %s' % error

            if success:
                success, error = poster.save_parse()
                print 'Save Parse actions is OK' if success else 'Save Parse Failed: %s' % error

    if options.launch:
        success, error = poster.load_parse()
        print 'Load Parse actions is OK' if success else 'Load Parse Failed: %s' % error

        if success:
            success, error = poster.launch()
            print 'Launch actions is OK' if success else 'Launch Parse Failed: %s' % error

    if options.wake:
        success, error = poster.wake(arguments, options)
        print 'Wake actions is OK' if success else 'Wake Failed: \'%s\' Does Not Exist' % error
    elif options.close:
        success, error = poster.close(arguments, options)
        print 'Close actions is OK' if success else 'Close Failed: \'%s\' Does Not Exist' % error

    if options.status:
        poster.status()

if __name__ == '__main__':
    main()
