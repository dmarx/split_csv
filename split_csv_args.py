import csv
import os
import argparse
import re
from operator import itemgetter

parser = argparse.ArgumentParser(description="Splits an Excel file into CSVs")
parser.add_argument('-c','--columns', type=int, nargs='+', help="Columns to be used as criteria for splitting file. First column = 0", required=True)
parser.add_argument('-f','--file',type=str, help="File to be split. If in same directory, can just be filename. Otherwise, be sure to give whole path.", required=True)
parser.add_argument('-s','--subdir',type=str, default=os.path.join(os.getcwd(),'csv'),help="Output subdirectory. Subdirectory must exist. Default = ./csv")
parser.add_argument('-a','--segregate',type=int, help="Field to define segregation of files. If this field is populated (or matches -b), files will be pulled aside")
parser.add_argument('-b','--segregateVal', help="Defines value for field segregations (see --segregate). Defaults to field being populated in anyway")
parser.add_argument('-x','--exclude',type=int, help="Field to exclude from results. If this field is populated (or matches -y) records will not be included in output file")
parser.add_argument('-y','--excludeVal', help="Field to define exclusion (-x). Defualts to being populated in any way")

args=parser.parse_args()
master_file = args.file
subdir= args.subdir

print args.file
print args.columns

with open(master_file, 'r') as f:
    reader = csv.reader(f, dialect='excel')
    maint_conf = []
    for row in reader:
        maint_conf.append(row)
        
#strip out unnecessary new line character at end of header record
maint_conf[0][0] = maint_conf[0][0][:-1]
    
def split_file_by_conf_key(disputes):
    '''Splits an input CSV into separate files based on the contents of two fields. 
    Requires that a CSV subdirectory exists in the filepath to write to.'''    
    header = disputes[0]
    dispute_records = disputes[1:]
    special_cases = {}
    # Let's start by sorting the file    
    dispute_records = sorted(dispute_records, key=itemgetter(*args.columns))
    i = -1
    next_conf_key = ''
    EOF = False
    #for row in dispute_records:        
    while True:   
        # initialize list to hold rows for new file
        this_file = []
        #this_file.append(header)
        while True:
            i+=1    # Row iterator    
            row = dispute_records[i]
            try:
                next_row=dispute_records[i+1]
            except:
                EOF = True  
                
            # Test if we should exclude the row
            if args.exclude <> None:
                if args.excludeVal == None and row[args.exclude] <> '':
                    continue
                elif row[args.exclude] == args.excludeVal:
                    continue 
            
            # Build conf_key and sort elements to ensure that we only produce one file between any two claimants
            if next_conf_key:
                conf_key = next_conf_key
            else:    
                conf = []            
                for c in args.columns:
                    if row[c] <> '':
                        conf.append(row[c])
                conf.sort()
                conf_key = ' & '.join(conf)
                conf_key = re.sub('[^A-Za-z0-9&!_\- ]','',conf_key)  # clean out most special characters and  
            
            #step ahead to the next row. If the conf_key's are different, we will generate the file (or append records).
            nconf = []
            for c in args.columns:
                if next_row[c] <> '':
                    nconf.append(next_row[c])
                nconf.sort()
                next_conf_key = ' & '.join(nconf)
                next_conf_key = re.sub('[^A-Za-z0-9&!_\- ]','',next_conf_key)  # clean out most special characters and    
                        
            # compare 'conf_key' for current row with last. If same, build file.  
            this_file.append(row)
            
            # Test if any rows in this file specify that it needs to be segregated. Can probably memoize this, but it doesn't really matter.
            if args.segregate <> None:
                if args.segregateVal == None:         #default behavior   
                    if row[args.segregate] <> '':
                        special_cases[conf_key+'.csv'] = 1
                else:
                    if row[args.segregate] == args.segregateVal:
                        special_cases[conf_key+'.csv'] = 1
                segregate = special_cases.keys()
            else: 
                segregate = None
            
            # Exit loop if we've accumulated all the rows for this file
            if EOF:
                break
            elif conf_key <> next_conf_key:
                break
                
        this_file_path = os.path.join(subdir, conf_key + '.csv')
        try:
            # test existence of file
            f = open(this_file_path,'r')
        except:
            f = open(this_file_path,'ab')
            writer = csv.writer(f, dialect='excel')
            writer.writerow(header)
        with open(this_file_path,'ab') as f: 
            writer = csv.writer(f, dialect='excel')
            #writer.writerow(row)
            for r in this_file:
                writer.writerow(r)
        # Segregate files with comments. Using dict data structure for deduping
        if EOF:
            return segregate


special_cases = split_file_by_conf_key(maint_conf)
src = subdir
dst = os.path.join(subdir,'special_cases')
if special_cases <> None:
    for file in special_cases:
        try:
            os.rename(os.path.join(src,file), os.path.join(dst,file))
        except OSError:
            os.mkdir(dst)
            os.rename(os.path.join(src,file), os.path.join(dst,file))