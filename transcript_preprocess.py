# %%
# Import necessary modules
from pydantic import BaseModel, Field
from typing import List, Dict, Any
import os
import re
import shutil
import pandas as pd
import instructor
import cohere
from datetime import datetime

# %%
# Load Cohere API key from a file
with open('cohere_api_key.txt', 'r') as key_file:
    cohere_api_key = key_file.readline().strip()

# Create an API client
client = instructor.from_cohere(cohere.Client(api_key=cohere_api_key))

# %%
# Define constants
UNPROCESSED_TRANSCRIPTS = "./transcripts/unprocessed/"  # Path to raw / unprocessed transcripts
RELEVANT_TRANSCRIPTS = "./transcripts/relevant_transcripts"  # Where to save transcripts identified as relevant
RELEVANT_SEGMENTS = "./transcripts/relevant_segments"  # Where to save relevant segments extracted from raw transcripts
ANNOTATED_TRANSCRIPTS = "./transcripts/annotated_transcripts"  # Where to save annotated transcripts
SEARCH_STRING = re.compile(r"\b(?:polio\S*\W(?:\w+\W+){0,10}?vaccin\S+|vaccin\S+\W+(?:\w+\W+){0,10}?polio\S*)\b")
CLIENT = instructor.from_cohere(cohere.Client(api_key="suwAosvqFJAr4zTEg6b3N05tovpr59K9YJqIkG6r"))
PROMPT = f"""\
Read the transcript of a podcast episode below and extract a StructuredDocument object from it where each section of the transcript is centered around a single concept/topic of conversation.
Each line of the transcript is marked with its line number in square brackets (e.g. [1], [2], [3], etc). Use the line numbers to indicate section start and end. Each line from the transcript must be assigned to one and only one section in the StructuredDocument object.
The start of each section must be the line in the transcript immediately following the line in the previous section end. For example, if the first section ended with the line numbered [3], the next section should begin with the line numbered [4].  
"""

# %%
# Define data structures
class Section(BaseModel):
    title: str = Field(description="main topic of this section of the document")
    start_index: int = Field(description="line number where the section begins")
    end_index: int = Field(description="line number where the section ends")

# %%
class StructuredDocument(BaseModel):
    """obtains meaningful sections, each centered around a single concept/topic"""
    sections: List[Section] = Field(description="a list of sections of the document")

# %%
# Define functions
def find_relevant_transcripts_deprecated(source, search_string, destination):
    """Finds relevant transcripts."""
    
    transcript_relevance = pd.DataFrame()
    transcript_ids = []
    relevance = []

    for filename in os.listdir(source):
        file_path = os.path.join(source, filename)
        filename_split = filename.split("_")
        file_id = filename_split[0]
        file = open(file_path, 'r')
        text = file.read()
        if search_string.search(text):
            print(str(file_id) + ": " + "relevant")
            transcript_ids.append(file_id)
            relevance.append(1)
            shutil.copy2(file_path, destination)
            print("Copied to target directory")
        else:
            print(str(file_id) + ": " + "not relevant")
            transcript_ids.append(file_id)
            relevance.append(0)
            
    transcript_relevance['unique_id'] = transcript_ids
    transcript_relevance['relevance'] = relevance

    return transcript_relevance


# %%
def find_relevant_transcripts(source, search_string, destination):
    """Finds relevant transcripts."""
    
    transcript_relevance = pd.DataFrame()
    transcript_ids = []
    relevance = []

    for filename in os.listdir(source):
        file_path = os.path.join(source, filename)
        filename_split = filename.split("_")
        file_id = filename_split[0]
        file = open(file_path, 'r')
        text = file.read().lower()
        if (search_string.search(text)) or \
            ((text.count('polio') > 1) and (text.count('vaccin') > 1)):
            print(str(file_id) + ": " + "relevant")
            transcript_ids.append(file_id)
            relevance.append(1)
            shutil.copy2(file_path, destination)
            print("Copied to target directory")
        else:
            print(str(file_id) + ": " + "not relevant")
            transcript_ids.append(file_id)
            relevance.append(0)
            
    transcript_relevance['unique_id'] = transcript_ids
    transcript_relevance['relevance'] = relevance

    return transcript_relevance

# %%
def doc_with_lines(document):
    document_lines = document.split(".")
    document_with_line_numbers = ""
    line2text = {}
    for i, line in enumerate(document_lines):
        document_with_line_numbers += f"[{i}] {line}\n"
        line2text[i] = line
    return document_with_line_numbers, line2text

# %%
def get_structured_document(document_with_line_numbers) -> StructuredDocument:
    return client.chat.completions.create(
        model="command-r-plus",
        response_model=StructuredDocument,
        messages=[
            {
                "role": "system",
                "content": PROMPT,
            },
            {
                "role": "user",
                "content": document_with_line_numbers,
            },
        ],
    ) # type: ignore

# %%
def get_sections_text(structured_doc, line2text):
    segments = []
    for s in structured_doc.sections:
        contents = []
        for line_id in range((s.start_index - 1), s.end_index):
            contents.append(line2text.get(line_id, ''))
        segments.append({
            "title": s.title,
            "content": "\n".join(contents),
            "start": s.start_index,
            "end": s.end_index
        })
    return segments

# %%
def check_create_new_dir(directory):
    """Creates a directory if it does not already exist.
    
    Args:
        directory: Path to the new directory.
    """

    if not os.path.exists(directory):
        os.mkdir(directory)

# %%
def extract_relevant_segments(unprocessed, relevant, annotated):
    """Extracts relevant segments from raw transcripts and saves in .txt file.
    Also creates  annotated version of transcript with segment titles.

    Args:
        unprocessed: Path to raw transcripts.
        relevant: Path to save extracted relevant segments.
        annotated: Path to save annotated transcripts. 
    """

    segment_relevance = pd.DataFrame()
    transcript_ids = []
    relevant_segments = []

    for filename in os.listdir(unprocessed):
        transcript_relevant = []
        transcript_annotated = []
        print("File name: " + str(filename))
        (shortname, extension) = os.path.splitext(filename)
        filename_split = filename.split("_")
        file_id = filename_split[0]
        transcript_ids.append(file_id)
        file_path = os.path.join(unprocessed, filename)
        file = open(file_path, 'r')
        text = file.read()
        file.close()
        document_with_line_numbers, line2text = doc_with_lines(text)
        structured_doc = get_structured_document(document_with_line_numbers)
        for item in structured_doc:
            print(item)
        segments = get_sections_text(structured_doc, line2text)
        print("Extracting relevant segments...")
        segments_relevant = []

        for segment in segments:
            title = segment['title']
            content = segment['content'].replace("\n", ".")
            transcript_annotated.append("## "+title)
            transcript_annotated.append(content)
            if content.count('polio') >= 1 and content.count('vaccin') >= 1:
                print(title+" relevant")
                transcript_relevant.append(content)
                segments_relevant.append(title)
            else:
                print(title+" not relevant")

        relevant_segments.append(segments_relevant)

        with open(relevant+"/"+shortname+"_relevant"+extension, "w") as output:
            for segment in transcript_relevant:
                output.write(segment+'\n')
        print("Saved relevant extracts")

        with open(annotated+"/"+shortname+"_annotated.md", "w") as output:
            for segment in transcript_annotated:
                output.write(segment+'\n\n')
        print("Saved annotated transcript")

    segment_relevance['unique_id'] = transcript_ids
    segment_relevance['relevant_segments'] = relevant_segments

    return segment_relevance

# %%
check_create_new_dir(RELEVANT_TRANSCRIPTS)

# %%
check_create_new_dir(RELEVANT_SEGMENTS)

# %%
check_create_new_dir(ANNOTATED_TRANSCRIPTS)

# %%
relevant_transcripts = find_relevant_transcripts(UNPROCESSED_TRANSCRIPTS, SEARCH_STRING, RELEVANT_TRANSCRIPTS)

# %%
relevant_transcripts

# %%
relevant_transcripts.relevance.value_counts()

# %%
# Save pre-processed data to Excel file
now = datetime.now()
datetime_string = now.strftime("%Y%m%d_%H%M%S")

output = relevant_transcripts.to_excel(
    "./data/clean/relevant_transcripts_"+datetime_string+".xlsx",
    index = False)

# %%
relevant_segments = extract_relevant_segments(RELEVANT_TRANSCRIPTS, RELEVANT_SEGMENTS, ANNOTATED_TRANSCRIPTS)

# %%
relevant_segments

# %%
# Save pre-processed data to Excel file
now = datetime.now()
datetime_string = now.strftime("%Y%m%d_%H%M%S")

output = relevant_segments.to_excel(
    "./data/clean/relevant_segments_"+datetime_string+".xlsx",
    index = False)


