from imports import *
import json
from langchain.docstore.document import Document
from faiss import (
    IndexFlatL2
)
from langchain_community.docstore.in_memory import (
    InMemoryDocstore
)

file_path = 'Data/individual_hospital.json'
with open(file_path, 'r') as file:
    data = json.load(file)

for item in data:
    visited=set()
    updated=[]
    for department in item['Medical Departments']:
        if department['Department'] not in visited:
            updated.append(department)
            visited.add(department['Department'])
    item['Medical Departments']=updated


rows = []
for item in data:
    for element in item['Medical Departments']:
        if 'Procedure Url' in element.keys():
            del element['Procedure Url']
    row = [
        "Hospital Name" + " " + str(item['Hospital Name']),
        "Hospital City" + " " + str(item['Hospital City']),
        "Hospital Country" + " " + str(item['Hospital Country']),
        "Hospital Beds" + " " + str(item['Hospital Beds']),
        "Established In" + " " + str(item['Established In']),
        "Speciality" + " " + str(item['Speciality']),
        "Hospital Address" + " " + str(item['Hospital Address']),
        "Team And Speciality" + " " + str(item['Team And Speciality']),
        "Top Doctors" + " " + str(item['Top Doctors']),
        "Infrastructure" + " " + str(item['Infrastructure']),
        "Location" + " " + str(item['Location']),
        "Facilities" + " " + str(item['Facilities']),
        "Medical Departments" + " " + str(item['Medical Departments'])
    ]
    rows.append(row)

docuemnts_list = []
for item in rows:
    docuemnts_list.append(Document(page_content=str(item), metadata={}))

embeddings = OpenAIEmbeddings()
db = FAISS(
    embedding_function=embeddings,
    index=IndexFlatL2(1536),
    docstore=InMemoryDocstore(),
    index_to_docstore_id={},
)
count=0
for doc in [text.page_content for text in docuemnts_list]:
    print(count," Done")
    db.add_texts([doc])
    count+=1

db.save_local("Data/CompleteHospitalsAndProcedureData")

