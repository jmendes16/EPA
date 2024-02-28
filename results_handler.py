import PyPDF2
import pandas as pd
import re
import psycopg2
from datetime import datetime

def extract_content(file_name: str) -> str:
    # return a string of all text in report
    with open(file_name, 'rb') as file:
        content = PyPDF2.PdfReader(file)

        output = ''

        for page_num in range(len(content.pages)):
            output += content.pages[page_num].extract_text()
        
    return output

# these next 3 functions rely on a consistent outputted string format from the extract_content function
def get_name(report: str) -> str:
    match = re.search(r'Apprentice name: (.*?) ULN:', report)
    return match.group(1).strip() if match else None

def get_ULN(report: str) -> str:
    match = re.search(r'ULN: (.*?) \nStandard:', report)
    return match.group(1).strip() if match else None

def get_assessment_date(report: str) -> datetime:
    match = re.search(r'Date of final \nassessment: (.*?) \nResults', report)
    date_string = match.group(1).strip() if match else None
    if date_string.find('th')>0:
        return datetime.strptime(date_string, '%dth %B %Y') if date_string else None
    elif date_string.find('nd')>0:
        datetime.strptime(date_string, '%dnd %B %Y') if date_string else None
    else:
        return datetime.strptime(date_string, '%dst %B %Y') if date_string else None

def get_KSBs(report: str) -> list:
    parts = report.split('Relevant KSBs')
    # making use of regex to identify KSBs
    return set(re.findall('[KSB][1-9]+', parts[1]))

# get comments from assessor
def get_comment(report: str) -> dict:
    output = {'Portfolio_Comment':'','Project_Comment':''}
    # sometimes these are in a different order
    if report.find('Professional Discussion :') < report.find('Project, Presentation and Q&A:'):    
        parts = report.split('Professional Discussion :')

        if len(parts) >= 2:
            discussion_parts = parts[1].split('Project, Presentation and Q&A:')    
            professional_discussion = discussion_parts[0].strip()
            output['Portfolio_Comment']=professional_discussion
            if len(discussion_parts) >= 2:
                discussion_parts = discussion_parts[1].split('PASS CRITERIA')
                project_discussion = discussion_parts[0].strip()
                output['Project_Comment']=project_discussion
    else:
        parts = report.split('Project, Presentation and Q&A:')

        if len(parts) >= 2:
            discussion_parts = parts[1].split('Professional Discussion :')    
            project_discussion = discussion_parts[0].strip()
            output['Project_Comment']=project_discussion

            if len(discussion_parts) >= 2:
                discussion_parts = discussion_parts[1].split('PASS CRITERIA')
                professional_discussion = discussion_parts[0].strip()
                output['Portfolio_Comment']=professional_discussion
        
    return output

# Collect all data into dataframe
def get_data(report: str) -> pd.DataFrame:
    data = {
        'Name':get_name(report),
        'ULN':get_ULN(report),
        'Assessment_Date':get_assessment_date(report),
        'KSBs':','.join([str(e) for e in get_KSBs(report)]),
        'KSB':[(get_KSBs(report)),],
        'Portfolio_Comment':get_comment(report)['Portfolio_Comment'],
        'Project_Comment':get_comment(report)['Project_Comment']
    }
    return pd.DataFrame(data, index=[0])

def database_transfer(data: pd.DataFrame, connection_string: str) -> None:
    apprentice_info = "INSERT INTO your_app_table (app_name, uln) VALUES (%s,%s);"
    report_summary = "INSERT INTO your_report_table (uln, assessment_date, ksbs, portfolio_comment, project_comment) VALUES (%s,%s,%s,%s,%s) RETURNING report_id"
    ksb_fails = "INSERT INTO your_ksb_table (report_id, ksb) VALUES (%s,%s)"

    conn = None
    config = connection_string

    try:
        with psycopg2.connect(config) as conn:
            with conn.cursor() as cur:
                # insert a new app_info
                cur.execute(apprentice_info, (
                    data.loc[0,'Name'],
                    data.loc[0,'ULN']
                ))

                # insert report summary
                cur.execute(report_summary, (
                    data.loc[0,'ULN'],
                    data.loc[0,'Assessment_Date'],
                    data.loc[0,'KSBs'],data.loc[0,
                    'Portfolio_Comment'],
                    data.loc[0,'Project_Comment']
                ))

                # get the report id
                row = cur.fetchone()
                if row:
                    report_id = row[0]
                else:
                    raise Exception('Could not get the part id')
                
                # collect individual ksbs
                for c in list(data.loc[0,'KSB']):
                    cur.execute(ksb_fails, (report_id, str(c)))

                # commit the transaction
                conn.commit()
    except psycopg2.errors.UniqueViolation:
            # This error occurs when there is a duplicate key.
            print(f"A duplicate key error occurred with ULN: {data.loc[0,'ULN']}")
            # skip this row and continue with the next row
            conn.rollback()
    except (Exception, psycopg2.DatabaseError) as error:
        if conn:
            conn.rollback()

        print(error)