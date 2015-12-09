# -*- coding: utf-8 -*-
from pymongo import MongoClient
import optparse
from settings import *


class FangZi(object):
    """
        This is a Class as dynamic-function_check-tool
        Base on MONGODB

        Image the situation, our web server receive a request from user,
          it contains a data and ask for checking if the data is available
          then we have many check to do in this data, some time we build lots of functions to do that just like
          the functions.py in examples/
          and some day we find the rule we build in the functions is not effective any more, so we change it,
          we add new functions, we remove old functions, we keep updating, we keep restarting our server for reload

        That is NOT ELEGANCE ENOUGH

        So Fang Zi is going to provide a new solution:
            we store all the check-function in database,
            we can update or remove or switch them by execute the database
            then how to use them?
            we use "exec" to execute the function-code, and we don't have to change checker any longer

            First, we use Fang Zi to parse code from functions source file,
            Second, we replace the "return Bool" with "result = Bool; raise Exception()"
            Third, we store it into database
            Fourth, we use a try-except structure to process the code, such as

            for code in all_functions:
                try:
                    exec code
                except:
                    return result

            Then we execute the check-function, and catch the result it raise

        That's what we made, a dynamic-function_check style to do the process

        Here's Some Usages:

            Basic parse and launch:
                parse_from_file()
                hull()
                save_parse()
                load_parse()
                launch()

            See Status:
                status()

            Wake up functions:
                set_status([function_names,], status=True)

            Close functions:
                set_status([function_names,], status=False)

            Remove functions:
                set_status([function_names,], remove=True)
    """

    # The MARKS in parse_temp
    # The structure is that
    # -----------FILE------------
    # |@IMPORT_BEGIN@           |
    # |import time              |
    # |...(something import)    |
    # |@IMPORT_END@             |
    # |                         |
    # |@STATIC_BEGIN@           |
    # |i_love_u = True          |
    # |...(something static)    |
    # |@STATIC_END@             |
    # |                         |
    # |@FUNC_BEGIN@             |
    # |@FUNC_HEAD_BEGIN@        |
    # |buy_me_the_coffee(money) |
    # |@FUNC_HEAD_END@          |
    # |@FUNC_CODE_BEGIN@        |
    # |...(the function code)   |
    # |@FUNC_CODE_END@          |
    # |@FUNC_SPLIT@             |
    # |...(another func part)   |
    # |@FUNC_SPLIT@             |
    # |...(another func part)   |
    # -----------FILE------------
    finder = {
        'IMPORT': ['@IMPORT_BEGIN@', '@IMPORT_END@'],
        'STATIC': ['@STATIC_BEGIN@', '@STATIC_END@'],
        'FUNC': ['@FUNC_BEGIN@', '@FUNC_END@',
                 '@FUNC_HEAD_BEGIN@', '@FUNC_HEAD_END@',
                 '@FUNC_CODE_BEGIN@', '@FUNC_CODE_END@',
                 '@FUNC_SPLIT@'],
        }

    def __init__(self, url=URL, port=PORT, database=DATABASE, collection=COLLECTION):
        """
            url: The MONGODB URL
            port: The MONGODB PORT
            database: The database name
            collection: Name of the collection of the database
        """

        # Make a Connection to MONGODB, give self.posts the collection
        conn = MongoClient(url, port)
        db = conn[database]
        self.posts = db[collection]

        # Initialize collectors
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

    def set_status(self, checkers, opt_all=False, opt_flag='', opt_group='', status=False, remove=False):
        """
            remove False:
                Wake or Close the functions in database
                Change the status between "Off" and "Working"
                Close doesn't delete any thing from database but just set the status "Off"
                So that we can control the functions' usage by the status

            remove True:
                remove functions from database

            usage:
                checkers: List of function names to change(wake/close/remove)
                opt: options object from main()
                     -a, --all: change all functions in database
                     -f, --flag: change or close all functions belongs to opt.flag in database
                     -g, --group: change or close all functions belongs to opt.group in database
                or change all functions in checkers
        """

        # Set all if needed
        if opt_all:

            # Remove or update control by "remove"
            self.posts.remove() if remove else \
                self.posts.update({}, {"$set": {"switch": status}}, multi=True)
            return True, ''

        # Set by flag if needed
        if opt_flag:
            if not self.posts.find_one({"flag": opt_flag}):
                    return False, 'Flag %s' % opt_flag

            # Remove or update control by "remove"
            self.posts.remove({'flag': opt_flag}) if remove else \
                self.posts.update({"flag": opt_flag}, {"$set": {"switch": status}}, multi=True)

        # Set by group if needed
        elif opt_group:
            if not self.posts.find_one({"group": opt_group}):
                    return False, 'Group %s' % opt_group

            # Remove or update control by "remove"
            self.posts.remove({'group': opt_group}) if remove else \
                self.posts.update({"group": opt_group}, {"$set": {"switch": status}}, multi=True)

        # Set by names in checkers
        else:
            for checker in checkers:
                if not self.posts.find_one({'_id': checker}):
                    return False, checker

            for checker in checkers:

                # Remove or update control by "remove"
                self.posts.remove({'_id': checker}) if remove else \
                    self.posts.update({"_id": checker}, {"$set": {"switch": status}})

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
            """
                Clean the NOTES in source file
                Only Clean the whole-line NOTE
                This type will not be cleaned: a = 1 # This is a statement
                Then return a no-notes source-file-lines
            """

            # Line in source file
            now_step = 0

            # Clean the NOTE begin with #
            while now_step + 1 <= len(now_lines):
                now_line = now_lines[now_step].replace(' ', '')
                if now_line and now_line[0] == '#':

                    # Find and remove the line
                    del now_lines[now_step]
                else:
                    now_step += 1

            # Reset the line
            now_step = 0

            # Clean the NOTE begin and end with """
            while now_step + 1 <= len(now_lines):
                now_line = now_lines[now_step].replace(' ', '')

                # Find the begin one
                if now_line.find("\"\"\"") > -1:
                    del now_lines[now_step]

                    # Remove all line between the two """
                    while now_lines[now_step].find("\"\"\"") == -1:
                        del now_lines[now_step]

                    # Find and remove the end one
                    del now_lines[now_step]
                else:
                    now_step += 1

            # Return the clean lines
            return now_lines

        def go_next(now_step):
            """
                Check the range and go next line
            """

            # Out of range
            if now_step + 1 >= len(lines):
                return now_step, False

            # Go next line
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
        """
            Handle the functions
            Store code part in self.func_collector[]
        """
        try:
            # Hull all func
            for index in range(0, len(self.func_collector)):
                self.func_collector[index][0] = self.huller(self.func_collector[index][0])
            return True, ''

        except Exception, e:
            return False, e

    @staticmethod
    def huller(string):
        """
            Remove the function head
            Change "return something" to "result = something; raise Exception(result)"
            and return a no-head & new-style function code
        """

        # Remove the 4-indent in code
        string = string.replace('\n    ', '\n')[string.find('\n')+1:]

        # The finder position
        pos_start = 0

        # Find all "return"
        while string.find('return ', pos_start) != -1:
            pos = string.find('\n', string.find('return ', pos_start))

            # Change and insert
            string = "%s;raise Exception(%s)%s" % (string[:pos], CATCHER, string[pos:])
            pos_start = pos + 1

        # Replace all "return" by "result ="
        string = string.replace('return', '%s =' % CATCHER)

        # Return the new style function code
        return string

    def parse_from_file(self, file_path=FILE_PATH):
        """
            Parse code from source file
        """

        try:
            source_code = open(file_path, 'r')
        except Exception, e:
            return False, e

        # Get source file lines
        lines = source_code.readlines()

        try:
            self.parse(lines)
        except Exception, e:
            return False, e

        return True, ''

    def parse_from_string(self, string=''):
        """
            Parse code from string
        """

        # Get source lines
        lines = string.split('\n')

        try:
            self.parse(lines)
        except Exception, e:
            return False, e

        return True, ''

    def save_parse(self):
        """
            After parse, we write the parse-result into file
            According to the finder[]
            It is easy to read and load
        """

        try:
            f = open('parse_temp', 'w')
        except Exception, e:
            return False, e

        # IMPORT PART
        f.write('%s\n' % self.finder['IMPORT'][0])
        f.write(self.import_collector)
        f.write('%s\n' % self.finder['IMPORT'][1])

        # STATIC PART
        f.write('%s\n' % self.finder['STATIC'][0])
        f.write(self.static_collector)
        f.write('%s\n' % self.finder['STATIC'][1])

        # FUNC PART
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
        """
            Before launch, we load the parse-result from file
            According to finder[]
            Read the information into self-attributes
        """

        f = open('parse_temp', 'r')
        raw_string = f.read()

        try:
            # Find IMPORT
            import_begin = raw_string.find(self.finder['IMPORT'][0])
            import_end = raw_string.find(self.finder['IMPORT'][1])

            # Check if the begin-end pair exist
            if (import_begin == -1) ^ (import_end == -1):
                raise Exception('Load Failed')

            # Find STATIC
            static_begin = raw_string.find(self.finder['STATIC'][0])
            static_end = raw_string.find(self.finder['STATIC'][1])

            # Check if the begin-end pair exist
            if (static_begin == -1) ^ (static_end == -1):
                raise Exception('Load Failed')

            # Find FUNC
            func_begin = raw_string.find(self.finder['FUNC'][0])
            func_end = raw_string.find(self.finder['FUNC'][1])

            # Check if the begin-end pair exist
            if (func_begin == -1) ^ (func_end == -1):
                raise Exception('Load Failed')

            # Get import
            if import_begin != -1:
                import_collector = raw_string[import_begin + len(self.finder['IMPORT'][0]): import_end]
            else:
                import_collector = ''

            # Get static
            if static_begin != -1:
                static_collector = raw_string[static_begin + len(self.finder['STATIC'][0]): static_end]
            else:
                static_collector = ''

            # Get functions
            func_collector = []
            if func_begin != -1:
                funcs = raw_string[func_begin + len(self.finder['FUNC'][0]): func_end].split(self.finder['FUNC'][6])

                # Get each one
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

            # Load to self-attributes at last
            self.import_collector = import_collector
            self.static_collector = static_collector
            self.func_collector = func_collector

            return True, ''

        except Exception, e:
            return False, e

    def submit(self, body, id_name, flag='Undefined', group='Undefined', switch=False, cover=False, **kwargs):
        """
            Submit one Document changes to database
            body: source code
            id_name: func-name or IMPORT or STATIC, as the "_id" in MONGODB
            flag: the flag
            group: the group
            switch: the status, True for Working, False for Off
            cover: if cover the database or not. True for removing all before the submit action
            **kwargs: the extra data to store in document
        """

        # Cover the database
        if cover:
            self.posts.remove({"_id": id_name})

        # Insert the _id for a new document if it doesn't exist
        if not self.posts.find_one({"_id": id_name}):
            self.posts.insert({"_id": id_name})

        # Make the data
        data = dict({"flag": flag,
                     "group": group,
                     "switch": switch,
                     "body": body}.items() + kwargs.items()
                    )

        # Insert into database
        self.posts.update({"_id": id_name}, {"$set": data})

    def launch(self):
        """
            Launch the parse-result
            There is IMPORT_POST, STATIC_POST and FUNC_POST which import from settings
            is to control that if we submit the part
        """

        try:
            if IMPORT_POST:
                self.submit(body=self.import_collector, id_name='IMPORT_PART', flag='IMPORT')
            if STATIC_POST:
                self.submit(body=self.static_collector, id_name='STATIC_PART', flag='STATIC')
            if FUNC_POST:
                for collector in self.func_collector:
                    self.submit(body=collector[0], id_name=collector[1], flag='CODE', para=collector[2])
            return True, ''

        except Exception, e:
            return False, e


def main():
    """
        Main for console line usage
    """

    # New poster
    poster = FangZi()

    # Set the options
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

    # Remove
    if options.remove:
        success, error = poster.set_status(arguments, options, remove=True)
        print 'Remove actions is OK' if success else 'Remove Failed: \'%s\' Does Not Exist' % error

    # Parse from file
    if options.parse:
        success, error = poster.parse_from_file()
        print 'Parse actions is OK' if success else 'Parse Failed: %s' % error

        if success:
            success, error = poster.hull()
            print 'Hull actions is OK' if success else 'Hull Failed: %s' % error

            if success:
                success, error = poster.save_parse()
                print 'Save Parse actions is OK' if success else 'Save Parse Failed: %s' % error

    # Launch
    if options.launch:
        success, error = poster.load_parse()
        print 'Load Parse actions is OK' if success else 'Load Parse Failed: %s' % error

        if success:
            success, error = poster.launch()
            print 'Launch actions is OK' if success else 'Launch Parse Failed: %s' % error

    # Wake or Close
    if options.wake:
        success, error = poster.set_status(checkers=arguments,
                                           opt_all=options.all,
                                           opt_flag=options.flag,
                                           opt_group=options.group,
                                           status=True)
        print 'Wake actions is OK' if success else 'Wake Failed: \'%s\' Does Not Exist' % error

    elif options.close:
        success, error = poster.set_status(checkers=arguments,
                                           opt_all=options.all,
                                           opt_flag=options.flag,
                                           opt_group=options.group,
                                           status=False)
        print 'Close actions is OK' if success else 'Close Failed: \'%s\' Does Not Exist' % error

    # Status
    if options.status:
        poster.status()

# Console line usage
if __name__ == '__main__':
    main()
