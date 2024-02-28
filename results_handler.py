import PyPDF2
import pandas as pd
import re
from datetime import datetime

def extract_content(file_name: str) -> str:
    with open(file_name, 'rb') as file:
        content = PyPDF2.PdfReader(file)

        output = ''

        for page_num in range(len(content.pages)):
            output += content.pages[page_num].extract_text()
        
    return output

def get_name(report: str) -> str:
    match = re.search(r'Apprentice name: (.*?) ULN:', report)
    return match.group(1).strip() if match else None

def get_ULN(report: str) -> str:
    match = re.search(r'ULN: (.*?) \nStandard:', report)
    return match.group(1).strip() if match else None

def get_assessment_date(report: str) -> datetime:
    match = re.search(r'Date of final \nassessment: (.*?) \nResults', report)
    date_string = match.group(1).strip() if match else None
    return datetime.strptime(date_string, '%dth %B %Y') if date_string else None

def get_KSBs(report: str) -> list:
    parts = report.split('Relevant KSBs')
    return set(re.findall('[KSB][1-9]+', parts[1]))

def get_comment(report: str) -> list:
    parts = report.split('Professional Discussion :')
    output = []

    if len(parts) >= 2:
        discussion_parts = parts[1].split('Project, Presentation and Q&A:')    
        professional_discussion = discussion_parts[0].strip()
        output.append(professional_discussion)

    if len(discussion_parts) >= 2:
        discussion_parts = discussion_parts[1].split('Project with Presentation & Questioning')
        project_discussion = discussion_parts[0].strip()
        output.append(project_discussion)
    
    return output

def get_data(report: str) -> pd.DataFrame:
    data = {
        'Name':get_name(report),
        'ULN':get_ULN(report),
        'Assessment_Date':get_assessment_date(report),
        'KSBs':','.join([str(e) for e in get_KSBs(report)]),
        'KSB':[(get_KSBs(report)),],
        'Portfolio_Comment':get_comment(report)[0],
        'Project_comment':get_comment(report)[1]
    }
    return pd.DataFrame(data, index=[0])