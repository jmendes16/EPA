import os

from results_handler import *

# you will also need to define your queries in the database transfer function in results_handler.py
path = 'path/to/your/file'
connection_string = "host=hostname dbname=databasename user=username password=password"

if __name__ == '__main__':

    # iterating over all files
    for filename in os.listdir(path):

        file_path = os.path.join(path, filename)
        _, extension = os.path.splitext(filename)

        # check if it's a pdf
        if extension == '.pdf':
            report = extract_content(str(file_path))
            data = get_data(report)
            database_transfer(data,connection_string)