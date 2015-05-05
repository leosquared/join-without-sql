import csv, sys, re, easygui as eg, operator
from os.path import basename

## GUI for opening file
def choose_file(msg='open file', title='open', filetypes=['*.csv', '*.txt']):
    """ Opens file """
    return eg.fileopenbox(msg=msg, default='~/Documents/*', filetypes=filetypes)

## Key for first table
def join_on(headers, sql_msg):
    """ Get 1 or more columns that contains the key to join on """
    cols = eg.multchoicebox(msg='From the 1st file, which columns contain the common data fields between the two files?{0}'.format(sql_msg), choices=headers)
    
    col_nums = []
    for col in cols:
        col_num = headers.index(col)
        col_nums.append(col_num)
    
    return col_nums

## Key for second table
def join_on_choice(headers, col_input):
    """ Get the mapping of each column from the first file to the second file """
    col_output = eg.choicebox(msg='Which column in the 2nd file does {0} map to?\n\na.{0} = b.'.format(col_input), choices=headers)
    
    return headers.index(col_output)

## Opens file, returns headers and content
def csv_open(file_path):
    raw_file = open(file_path, 'rU')
    delim = csv.Sniffer().sniff(raw_file.readline())
    raw_file.seek(0)
    
    file = csv.reader(raw_file, dialect = delim)
    headers = file.next()
    
    return headers, file, basename(raw_file.name)

## select only specified elements from a list
def get_items(row, indexes):
    return map(lambda x: x[1], filter(lambda (i, x): i in indexes, enumerate(row)))

## Let user choose columns
def choose_columns(headers1, headers2, sql_msg):
    all_headers = map(lambda x: 'a.'+x, headers1) + map(lambda x: 'b.'+x, headers2)
    
    columns_chosen = eg.multchoicebox(msg='Choose the columns you want to export{0}'.format(sql_msg), choices=all_headers)
    sql_msg += ' '
    sql_msg += ', '.join(columns_chosen)
    
    indexes1 = []
    indexes2 = []
    for column in columns_chosen:
        if column[0:1] == 'a':
            indexes1.append(headers1.index(column[2:]))
        elif column[0:1] == 'b':
            indexes2.append(headers2.index(column[2:]))
        else:
            continue
    
    return indexes1, indexes2, sql_msg


## Main function
def run_join(file_path1, file_path2):
    headers1, file1, file_name1 = csv_open(file_path1)
    headers2, file2, file_name2 = csv_open(file_path2)
    
    sql_msg = '\n\nSELECT'
    
    indexes1, indexes2, sql_msg = choose_columns(headers1, headers2, sql_msg)
    sql_msg += '\n\nFROM {0} a\n\nLEFT JOIN {1} b \nON a.'.format(file_name1, file_name2)
    
    lu_cols1 = join_on(headers1, sql_msg)
    
    
    lu_cols2 = []
    for i, col1 in enumerate(lu_cols1):
        col2 = join_on_choice(headers2, headers1[col1])
        lu_cols2.append(col2)
        sql_msg += ' a.{0} = b.{1}'.format(headers1[col1], headers2[col2]) if i == 0 else ' AND a.{0} = b.{1}'.format(headers1[col1], headers2[col2])
    
    
    lu = {}
    for row in file2:
        try:
            lu_id = ''.join(row[x] for x in lu_cols2)
            if not lu.get(lu_id):
                lu[lu_id] = [row]
            else:
                lu[lu_id].append(row)
        except:
            print row
    
    count_rows = 0
    count_matches = 0
    data = []
    for row in file1:
        try:
            id = ''.join(row[x] for x in lu_cols1)
            cur_row = row
        except:
            print row
            id= 1
            cur_row=row
        
        if not lu.get(id) or lu.get(id) == '':
            new_row = get_items(cur_row, indexes1)
            data.append(new_row)
            count_rows += 1
        else:
            for match in lu.get(id):
                new_row = get_items(cur_row, indexes1) + get_items(match, indexes2)
                data.append(new_row)
                count_matches += 1
                count_rows += 1
    
    return headers1, headers2, data, count_rows, count_matches, indexes1, indexes2

start = """
Welcome! You will be asked to open two files to merge together.
Remember, the first file is your main file (like a LEFT JOIN).
"""
eg.msgbox(msg=start)
file1 = choose_file('Please Select the First File')
file2 = choose_file('Please Select the Second File')

headers1, headers2, out_data, count_rows, count_matches, indexes1, indexes2 = run_join(file1, file2)
eg.msgbox(msg='The file generated {0} rows, {1} matched!!'.format(count_rows, count_matches))
out_file = csv.writer(open(eg.filesavebox(msg='Save Result As: (Make Sure to inlude .csv)', default=(file1.replace('.', '_')+'_matched.csv'), filetypes=['*.csv', '*.txt']), 'w'))
write_headers = get_items(headers1, indexes1) + get_items(headers2, indexes2)

out_file.writerow(write_headers)
out_file.writerows(out_data)