#!/usr/bin/python

"""
goal, feed in moquery output from text, json, or xml
and create local dict that we can walk through and print FULL
record matching user provided regex string

    - xml parse failure:
        snmp string with '&' character at at end
        cat file.xml | 
          sed 's/&\]/\]/g' | sed 's/&"/"/g' | sed 's/-</-/g' | sed 's/>\]/\]/g'
          > clean_file.xml

@author agossett@cisco.com
@version 09/08/2015

5/10/2019 - added retro support and python3 - apeacock@cisco.com
"""

import logging, re, json, time
import xml.etree.ElementTree as ET

# override sort with natsort if available
try:    
    from natsort import natsorted as sorted
except: pass
    

def td(start, end, milli=True):
    """
    create constant delta timestamp string between two floats 'start' and 'end'
    timestamps created by user calling time.time()
    """
    delta = end - start
    if milli: s = "{0:.3f} msecs".format(delta*1000)
    else: s = "{0:.3f} secs".format(delta)
    return s

def dump_entries(entries):
    """
    dump entries in json file so user can save/redirect to a file
    Note - entries is a list so will create a dict wrapper for easy 
    import/export
    """
    j = {"entries": entries}
    print(json.dumps(j))

def restore_entries(input_file):
    """
    rebuild entries from provided 'dump' file
    """
    start = time.time()
    j = json.load(input_file)
    if "entries" in j:
        logging.debug("restore time: %s" % td(start, time.time()))
        logging.debug("restore entries: %s" % len(j["entries"]))
        return j["entries"]
    else:
        raise Exception("Restore file not correctly formatted")

def search_entries(entries, regex, ignore_case=False, sort_reg=None, 
        sort_neg=False, retro_option=False, retro_space=False, retro_month=False, retro_full=False,
        retro_deletion=False):
    """
    loop through entries list and print each full entry that matches regex
    """

    results = []
    logging.debug("regex: %s, ignore_case: %r, negative: %r" % (regex, ignore_case, sort_neg))
    start = time.time()
    matches = 0
    if ignore_case and regex is not None:
        for e in entries:
            matched = False
            if re.search(regex, e, re.IGNORECASE):
                matches+=1
                matched=True
            if (matched and not sort_neg) or (not matched and sort_neg):
                results.append(e)
    elif regex is not None:
        for e in entries:
            matched = False
            if re.search(regex, e):
                matches+=1
                matched=True
            if (matched and not sort_neg) or (not matched and sort_neg):
                results.append(e)
    else:
        # get all entries
        results = entries

    logging.debug("search time: %s" % td(start, time.time()))
    logging.debug("search matches: %d" % matches)
    if len(results) == 0:
        logging.debug("no results to print")
        return
    
    # sort the 'filtered' results into final result list
    final_results = []
    if sort_reg is not None:
        logging.debug("sort_reg: %s" % sort_reg)
        sort_match_count = 0
        start = time.time()
        ts_results_default = []     # catch all if we don't match any results
        ts_results = {}
        for r in results:
            r1 = re.search(sort_reg, r)
            if r1 is not None:
                sort_match_count+= 1
                m = r1.group("m")
                if m not in ts_results: 
                    ts_results[m] = []
                ts_results[m].append(r)
            else:
                ts_results_default.append(r)
        # final results is combined ts_results_default and sorted results
        final_results = ts_results_default
        for k in sorted(ts_results):
            final_results+= ts_results[k]
        logging.debug("sort attribute time: %s" % td(start, time.time()))
        logging.debug("sort attribute matches: %d" % sort_match_count)
    else:
        final_results = results

    # print all results (peek first for suppot for retro_peek)
    if retro_option:
        retro_peek = results[0].splitlines()[0]
        if "# aaaModLR" in retro_peek:
            new_results = aaa_entry_parse(final_results, retro_full)
        elif "# eventRecord" in retro_peek:
            new_results = event_entry_parse(final_results, retro_full)
        elif "# faultRecord" in retro_peek:
            new_results = fault_entry_parse(final_results, retro_full, retro_deletion)
        else:
            logging.error("Unable to Determine Record Type")
            new_results = final_results

        if retro_space:
            new_results = space_option(new_results)
        for e in new_results:
            if retro_month:
                print(letter_month(e))
            else:
                print(e)
    # normal non-retro printing
    else:
        for r in final_results:
            print("".join(r))
  
def build_from_text(input_file, start_reg="^#[ \t]+[\w]+", 
        allow_empty_lines=False):
    """ 
    receives file pointer to text input and breaks into entries list
    default start_reg set to moquery regex
    """
    logging.debug("build from test regex: \"%s\"" % start_reg)
    start = time.time()
    entries = []
    entry = None
    for l in input_file:
        r1 = re.search(start_reg, l)
        if r1 is not None:
            if entry is None:
                entry = [l]
            else:
                entries.append("".join(entry))
                entry = [l]
        elif entry is not None:
            # if empty line, then end this entry
            if not allow_empty_lines and len(l.strip())==0:
                entries.append("".join(entry))
                entry = None
            else:
                entry.append(l)

    # ensure we catch the last entry as well
    if entry is not None:
        entries.append("".join(entry))

    # return the result
    logging.debug("build entries time: %s" % td(start, time.time()))
    logging.debug("entries built from text: %s" % len(entries))
    return entries
                

def build_from_json(input_file):
    """ 
    receives file pointer to moquery json input and breaks into entries list
    """
    start = time.time()
    root = json.load(input_file)
    logging.debug("json load time: %s" % td(start, time.time()))

    entries = []
    start = time.time()
    if "imdata" in root:
        for c in root["imdata"]:
            logging.debug("c is %s"%c)
            __build_json_child(entries, c, 1)
    else:
        __build_json_child(entries, root)
    
    logging.debug("build entries time: %s" % td(start, time.time()))
    logging.debug("entries built from json: %s" % len(entries))
    return entries


def __build_json_child(entries, node, depth=0):
    """ recursive function to grab tags/attrib from all children json nodes """
    max_depth=10000
    if depth > max_depth:
        err = "recursive loop? build child depth exceeds maximum depth %d" % (
            max_depth)
        raise Exception(err)
  
    entry = []
    keys = list(node.keys())
    if len(keys)!= 1:
        raise Exception("unexpected key count for node: %s" % node)
    
    logging.debug("keys is type %s"%type(keys))
    logging.debug("keys is %s"%keys)
        
    entry.append("# %s\n" % keys[0])
    n = node[keys[0]]
    if "attributes" in n:
        attr = n ["attributes"]
        for a in attr:
            entry.append('{0:<16}: {1}\n'.format(a, attr[a]))
    else:
        raise Exception("node with no attributes: %s" % node)

    # add entry to entries list
    entries.append("".join(entry))

    next_depth = depth+1
    if "children" in n:
        if type(n["children"]) is list:
            for child in n["children"]:
                __build_json_child(entries, child, next_depth)
        else:
            err = "children type (%s) for node is not a list.  Node: %s" % (
                str(type(n["children"])), n)
            raise Exception(err)


def build_from_xml(input_file):
    """ 
    receives file pointer to moquery xml input and breaks into entries list
    """
    start = time.time()
    tree = ET.parse(input_file)
    logging.debug("xml ET parse time: %s" % td(start, time.time()))
    
    entries = []
    start = time.time()
    root = tree.getroot()
    # the root is generally 'imdata' which we don't need
    if root.tag == "imdata":
        for child in root:
            __build_xml_child(entries, child, 1)
    else:
        __build_xml_child(entries, root)
    logging.debug("build entries time: %s" % td(start, time.time()))
    logging.debug("entries built from xml: %s" % len(entries))
    return entries
    
def __build_xml_child(entries, node, depth=0):
    """ recursive function to grab tags/attrib from all children xml nodes """
    max_depth=10000
    if depth > max_depth:
        err = "recursive loop? build child depth exceeds maximum depth %d" % (
            max_depth)
        raise Exception(err)

    entry = []
    entry.append("# %s\n" % node.tag)
    for a in node.attrib:
        entry.append('{0:<16}: {1}\n'.format(a, node.attrib[a]))
    entries.append("".join(entry))

    next_depth = depth+1
    for child in node:
        __build_xml_child(entries, child, next_depth)
    
def letter_month(whole_string):
    """
    this function expects the whole string that is already parsed by entry_parsed
    """
    letter_date = ""
    month = ""
    new_month = ""
    date_reg = re.compile("^20[0-5][0-9]-[0-1][0-9]-[0-3][0-9]")    

    # get the date_string from the whole_string
    date_string = re.search(date_reg, whole_string)
    if date_string:
       date_string = date_string.group(0)
    else:
        return whole_string    

    # get the two digit month from the date_string
    month = date_string[5:7]
    
    if month == "01": new_month = "Jan"
    if month == "02": new_month = "Feb"
    if month == "03": new_month = "Mar"
    if month == "04": new_month = "Apr"
    if month == "05": new_month = "May"
    if month == "06": new_month = "Jun"
    if month == "07": new_month = "Jul"
    if month == "08": new_month = "Aug"
    if month == "09": new_month = "Sep"
    if month == "10": new_month = "Oct"
    if month == "11": new_month = "Nov"
    if month == "12": new_month = "Dec"
    
    letter_date = date_string[0:4] + " " + new_month + " " + date_string[8:10] + " "
    
    out_string = letter_date + whole_string[11:]    

    return out_string


def event_entry_parse(input_file, full_option):
    """
    parse each entry and return the list of new entries, use STDIN

    """
    out_list = []

    created_reg = re.compile("(?<=created\s{9}:\s).*")
    severity_reg = re.compile("(?<=severity\s{8}:\s).*")
    affected_reg = re.compile("(?<=affected\s{8}:\s).*")
    trig_reg = re.compile("(?<=trig\s{12}:\s).*")
    descr_reg = re.compile("(?<=descr\s{11}:\s).*")
    changeSet_reg = re.compile("(?<=changeSet\s{7}:\s).*")
    
    created = ""
    severity = ""
    trig = ""
    affected = ""
    descr = ""
    changeSet = ""

    for item in input_file:
        for line in item[0].splitlines() if isinstance(item,list) else item.splitlines():
            if "# eventRecord" in line: 
                created = "unknown"
                severity = "unknown"
                trig = "unknown"
                affected = "unknown"
                descr = "unknown"
                changeSet = "unknown"
                continue
            if "created" in line:                
                this = re.search(created_reg, line)
                if this:
                    created_pre = this.group(0)
                    created = created_pre[0:10] + " " + created_pre[11:23]
            if "severity" in line:
                this = re.search(severity_reg, line)
                if this: severity = this.group(0)
            if "trig" in line:
                this = re.search(trig_reg, line)
                if this: trig = this.group(0)
            if "affected" in line:
                this = re.search(affected_reg, line)
                if this:
                    if full_option:
                        affected = this.group(0)
                    else:
                        affected = this.group(0)
                        if len(affected) >= 40:
                            affected = "..." + affected[:40]
            if "descr" in line:
                this = re.search(descr_reg, line)
                if this: descr = this.group(0)
            if "changeSet" in line:
                this = re.search(changeSet_reg, line)
                if this.group(0).strip(): changeSet = this.group(0) 
        
        out_line = "%s %s %s %%%s: \"\"%s\"\"" %(created, severity, trig, affected, descr)
        if changeSet.strip() != "unknown": out_line = out_line + " == " + changeSet
        out_list.append(out_line)

    return out_list


def aaa_entry_parse(input_file, full_option):
    """
    parse each entry and return the list of new entries, use STDIN

    """
    out_list = []

    created_reg = re.compile("(?<=created\s{9}:\s).*")
    user_reg = re.compile("(?<=user\s{12}:\s).*")
    affected_reg = re.compile("(?<=affected\s{8}:\s).*")
    descr_reg = re.compile("(?<=descr\s{11}:\s).*")
    changeSet_reg = re.compile("(?<=changeSet\s{7}:\s).*")
    
    created = ""
    user = ""
    affected = ""
    descr = ""
    changeSet = ""

    for item in input_file:
        for line in item[0].splitlines() if isinstance(item,list) else item.splitlines():
            if "# aaaModLR" in line:
                created = "unknown"
                user = "unknown"
                affected = "unknown"
                descr = "unknown"
                changeSet = "unknown"
                continue
            if "created" in line:                
                this = re.search(created_reg, line)
                if this:
                    created_pre = this.group(0)
                    created = created_pre[0:10] + " " + created_pre[11:23]
            if "user" in line:
                this = re.search(user_reg, line)
                if this: user = this.group(0)
            if "affected" in line:
                this = re.search(affected_reg, line)
                if this:
                    if full_option:
                        affected = this.group(0)
                    else:
                        affected = this.group(0)
                        if len(affected) >= 50:
                            affected = affected[:50] + "..."
            if "descr" in line:
                this = re.search(descr_reg, line)
                if this: descr = this.group(0)
            if "changeSet" in line:
                this = re.search(changeSet_reg, line)
                if this.group(0).strip(): changeSet = this.group(0) 
            
        out_line = "%s %s %%%s: \"\"%s\"\"" %(created, user.strip("remote_user-"), affected, descr)
        if changeSet.strip() != "unknown": out_line = out_line + " == " + changeSet
        out_list.append(out_line)
        
    return out_list


def fault_entry_parse(input_file, full_option, del_option):
    """
    parse each entry and return the list of new entries, use STDIN

    """
    out_list = []

    created_reg = re.compile("(?<=created\s{9}:\s).*")
    code_reg = re.compile("(?<=code\s{12}:\s).*")
    o_severity_reg = re.compile("(?<=origSeverity\s{4}:\s).*")
    severity_reg = re.compile("(?<=severity\s{8}:\s).*")
    affected_reg = re.compile("(?<=affected\s{8}:\s).*")
    lc_reg = re.compile("(?<=lc\s{14}:\s).*")
    ind_reg = re.compile("(?<=ind\s{13}:\s).*")
    descr_reg = re.compile("(?<=descr\s{11}:\s).*")
    changeSet_reg = re.compile("(?<=changeSet\s{7}:\s).*")
    
    code = ""
    created = ""
    o_severity = ""
    severity = ""
    lc = ""
    affected = ""
    descr = ""
    changeSet = ""
    ind = ""

    for item in input_file:
        for line in item[0].splitlines() if isinstance(item,list) else item.splitlines():
            if ("# faultRecord" in line) or ("# faultInst" in line): 
                code = "unknown"
                created = "unknown"
                o_severity = "unknown"
                severity = "unknown"
                lc = "unknown"
                affected = "unknown"
                descr = "unknown"
                changeSet = "unknown"
                ind = "unknown"
                continue
            if "created" in line:                
                this = re.search(created_reg, line)
                if this:
                    created_pre = this.group(0)
                    created = created_pre[0:10] + " " + created_pre[11:23]
            if "ind   " in line:
                this = re.search(ind_reg, line)
                if this: ind = this.group(0)
            if "code  " in line:
                this = re.search(code_reg, line)
                if this: code = this.group(0)
            if "origSeverity" in line:
                this = re.search(o_severity_reg, line)
                if this:  o_severity = this.group(0)
            if "severity  " in line:
                this = re.search(severity_reg, line)
                if this: severity = this.group(0)
            if "lc  " in line:
                this = re.search(lc_reg, line)
                if this: lc = this.group(0)
            if "affected  " in line:
                this = re.search(affected_reg, line)
                if this:
                    if full_option:
                        affected = this.group(0)
                    else:
                        affected = this.group(0)
                        if len(affected) >= 40:
                            affected = "..." + affected[:40]
            if "descr  " in line:
                this = re.search(descr_reg, line)
                if this: descr = this.group(0)
            if "changeSet" in line:
                this = re.search(changeSet_reg, line)
                if this.group(0).strip(): changeSet = this.group(0) 
        
        out_line = "%s %s '%s' %s/%s %%%s: \"\"%s\"\"" %(created, code, lc, o_severity, severity, affected, descr)
        if changeSet.strip() != "unknown": out_line = out_line + " == " + changeSet
        if del_option:
            out_list.append(out_line)
        else:
            if not ind=="deletion":
                out_list.append(out_line)
        
    return out_list


def space_option(input_list):
    """
    add a grouping option to make it easier to read discern the difference between user input and
    automated input the thought is that a user cannot do anything subsecond, so any aaa logs that
    are >1 must be a part of another action I'm just comparing the minutes and seconds so there
    would be scenarios where commands run on different dates at the exact same second would appear
    as one entry, but that seems like a rare occurance 
    """   
    out_list = []
    last_time = 235959  # by using a decimal, we can just compare and see if the difference is >2 (seconds)
    this_time = 235959
    time_reg = re.compile("(?<=^20[0-5][0-9]-[0-1][0-9]-[0-3][0-9]\s)[0-2][0-9]:[0-5][0-9]:[0-5][0-9]")
    first_time = True
    spacing_time = 3  # time in seconds we need to not see a log to create a space

    for line in input_list:
        this_time = re.search(time_reg, line)
        if this_time:
            this_time = int(this_time.group(0).replace(":", ""))
        if not first_time:
            if abs(this_time-last_time) >= spacing_time:
                out_list.append("")
        out_list.append(line )
        if first_time: first_time = False
        last_time = this_time
    
    return out_list


def letter_month(whole_string):

    letter_date = ""
    month = ""
    new_month = ""
    date_reg = re.compile("^20[0-5][0-9]-[0-1][0-9]-[0-3][0-9]")    

    # get the date_string from the whole_string
    date_string = re.search(date_reg, whole_string)
    if date_string:
       date_string = date_string.group(0)
    else:
        return whole_string    

    # get the two digit month from the date_string
    month = date_string[5:7]
    
    if month == "01": new_month = "Jan"
    if month == "02": new_month = "Feb"
    if month == "03": new_month = "Mar"
    if month == "04": new_month = "Apr"
    if month == "05": new_month = "May"
    if month == "06": new_month = "Jun"
    if month == "07": new_month = "Jul"
    if month == "08": new_month = "Aug"
    if month == "09": new_month = "Sep"
    if month == "10": new_month = "Oct"
    if month == "11": new_month = "Nov"
    if month == "12": new_month = "Dec"
    
    letter_date = date_string[0:4] + " " + new_month + " " + date_string[8:10] + " "
    
    out_string = letter_date + whole_string[11:]    

    return out_string


if __name__ == "__main__":

    import argparse, sys, os

    desc = """
    takes raw input from --file or piped from standard in.  Can also provide
    previously parsed object via --restore option

    Added retro functionality to parse logs and return a one line entry.

    --retro option now automatically detects record type

    Ex:

    section_parser --xml --file aaaModLR --retro --month --space

    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-r", "--regex", action="store", dest="regex",
        help="print all entries that match search regex")
    parser.add_argument("--negative", action="store_true", dest="nregex",
        help="print all entries that do not match search regex")
    parser.add_argument("-i", "--ignore-case", action="store_true", 
        dest="ignore_case", help="case insensitive search")
    parser.add_argument("--sort", action="store", dest="sort",
        help="sort results based on provided attribute")
    parser.add_argument("--sortr", action="store", dest="sortr",
        help="sort results based on value matched from provided regex")
    parser.add_argument("--file", action="store", help="filename", 
        dest="file", nargs="+")
    parser.add_argument("--restore", action="store", help="saved output list",
        dest="restore")
    parser.add_argument("--dump", action="store_true", 
        help="dump entries in json format", dest="dump")
    parser.add_argument("--xml", action="store_true", 
        help="input in xml format", dest="xml")
    parser.add_argument("--json", action="store_true", 
        help="input in json format", dest="json")
    parser.add_argument("--moquery", action="store_true", 
        help="input in moquery text format (default)", dest="moquery")
    parser.add_argument("--text", action="store_true", 
        help="input any text format", dest="text")
    parser.add_argument("--delim", action="store", dest="delim",
        help="delimiter for sections in text file", 
        default="^[ \t]*\[[0-9]+ [^\]]+\]")
    parser.add_argument("--allow-empty", action="store_true", 
        dest="allow_empty",
        help="allow empty lines within a section")
    parser.add_argument("--retro", action="store_true", dest="retro_option",
        help="retro argument, will auto-detect aaa, fault, or event")
    parser.add_argument("--space", action="store_true", dest="retro_space",
        help="space argument for retro, adds a space after 5 seconds of inactivity")
    parser.add_argument("--month", action="store_true", dest="retro_month",
        help="converts the month from a number into a 3 letter abbreviation")
    parser.add_argument("--full", action="store_true", dest="retro_full",
        help="prints the full output, default is only 40 characters")
    parser.add_argument("--deletion", action="store_true", dest="retro_deletion",
        help="option to print faults that are in deletion state, which are suppressed by default")
    parser.add_argument("--debug", action="store", help="debug level",
        dest="debug", default="ERROR")

    args = parser.parse_args()

    # configure logging
    logger = logging.getLogger("")
    logger.setLevel(logging.WARN)
    logger_handler = logging.StreamHandler(sys.stdout)
    fmt ="%(asctime)s.%(msecs).03d %(levelname)8s %(filename)"
    fmt+="16s:(%(lineno)d): %(message)s"
    logger_handler.setFormatter(logging.Formatter(
        fmt=fmt,
        datefmt="%Z %Y-%m-%d %H:%M:%S")
    )
    logger.addHandler(logger_handler)

    # set debug level
    args.debug = args.debug.upper()
    if args.debug == "DEBUG": logger.setLevel(logging.DEBUG)
    if args.debug == "INFO": logger.setLevel(logging.INFO)
    if args.debug == "WARN": logger.setLevel(logging.WARN)
    if args.debug == "ERROR": logger.setLevel(logging.ERROR)


    # determine whether to use xml or json pretty print method
    method = None
    if args.moquery: method = "moquery"
    elif args.text: method = "text"
    elif args.xml: method = "xml"
    elif args.json: method = "json"
    else: method = "moquery"

    # entries to run searches against
    entries = []

    # since we're using try/finally to ensure correct file closure, we need a 
    # flag to indicate whether or not to proceed with dump/search
    sys_exited = False    

    try:
        # if restore option, use user provided file for input
        if args.restore is not None:
            with open(args.restore, "r") as f:
                entries = restore_entries(f)
        else:
            # get data from file or stdin and write to output file or stdout
            ifiles = []
            in_file = None
            if args.file is not None:
                # args.file is a list of files, need to check each one
                flist = []
                for af in args.file:
                    if os.path.isfile(af):
                        # grab specific file
                        flist.append(af)
                    elif os.path.isdir(af):
                        # grab all files in directory
                        for df in os.listdir(af):
                            if os.path.isfile(os.path.join(af, df)):
                                flist.append(os.path.join(af, df))

                try:
                    #in_file = open(args.file, "r")
                    for af in flist:
                        ifiles.append(open(af, "r"))
                except:
                    import traceback
                    traceback.print_exc()
                    sys.exit()
            # no file was provided, try to read from stdin
            else: 
                in_file = sys.stdin
                ifiles = [in_file]
                # ensure that stdin is only used if output redirected to this 
                # script
                if in_file.isatty(): 
                    parser.print_help()
                    sys.exit()

            # support multiple files, parse each individually and append to 
            # entries list
            for f in ifiles:
                # execute method
                if method == "moquery": entries+= build_from_text(f)
                elif method == "text": 
                    entries+= build_from_text(f, args.delim, args.allow_empty)
                elif method == "xml": entries+= build_from_xml(f)
                elif method == "json": entries+= build_from_json(f)
                else:
                    raise Exception("invalid method: %s" % method)

    except SystemExit:
        # do nothing if sys.exit was manually called
        sys_exited = True
    except:
        import traceback
        traceback.print_exc() 
        sys_exited = True
    finally:
        # try to close input and output files
        # note, this can be closing stdin or stdout so don't attempt
        # to read/write (i.e., 'print') after they are closed
        try:
            if in_file is not None: in_file.close()
        except: pass

    # force an exit if it was hit in the try/finally
    if sys_exited: sys.exit()

    # build sort regex based on provided arguments
    sortr = None
    if args.sort is not None:
        sortr = "%s[ \t]*:[ \t]*(?P<m>[^ \n]+)" % args.sort
    elif args.sortr is not None:
        sortr = "(?P<m>%s)" % args.sortr

    # dump entries if user requested it 
    # (for reuse of existing file with re-parsing each time)
    if args.dump:
        dump_entries(entries)

    # execute search against entries and print WHOLE entry on match
    elif args.regex:
        search_entries(entries, args.regex, args.ignore_case, sortr,args.nregex, args.retro_option,
        args.retro_space, args.retro_month, args.retro_full, args.retro_deletion)
    # no regex provided - just print all entries with user's sort option
    else:
        search_entries(entries, None, None, sortr, args.nregex, args.retro_option, args.retro_space,
        args.retro_month, args.retro_full, args.retro_deletion)

