import json
import os
import ast
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import OpenAI

os.environ['OPENAI_API_KEY']='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'
def extract_information_from_image(base64_image):
    from openai import OpenAI
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "Extract and return all the Text from the Given Image. wihtout any prefix or PostFix Only Exracted Text."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
    )
    resul = response.json()
    json_loaded = json.loads(resul)
    return f"{json_loaded['choices'][0]['message']['content'] }"

def extract_data_and_schedule_appointment_followup(chat_history,hcf_id,session,leads_and_followup_status):
  template = """
  
  You are Information summarizer and your Task is to SUmmarize and Collect information from the Given Conversation History and repond as JSON.
  
  Information required:
  username: Name of the Patient or the person being interacting if present else empty string
  email_address: user email address provided in the Conversation
  medical_procedure_name: medical procedure that user want to avail.
  preferred_city: preferred city in given country where user wants to do the procedure.
  preferred_country: preferred country in which the user wants to do the procedure.
  important_concerns: any concerns or important details users mentioned or want us to know.
  summary: briefly summarize the whole conversation.
  
  Response Structure:
  Your response should be strictly in JSON format. Exclude any additional text or commentary. Just return JSON that can be directly parsed using json.loads() without any errors.
  Must include all attribute if the exists or not.
  
  output structure:
  {{
  "username":"user name as string if exists else empty string",
  "email_address": "email address as string if exists else empty string",
  "medical_procedures_name": "comma splitted medical procedures names that user want to avail if exists else empty string.",
  "preferred_country": "preferred country in which the user wants to do the procedure if exists else empty string",
  "preferred_city": "preferred city in given country where user wants to do the procedure if exists else empty String",
  "important_concerns": "Important concerns if exists else empty string",
  "Preferred_Date": "Preferred Date of procedure if exists else empty string",
  "summary": "briefly summarize the whole conversation."
  }}
  
  Conversation among user and AI Agent:
  {chat_history}
  
  """
  prompt_template = PromptTemplate(template=template,
                                   input_variables=["chat_history"])
  chain = LLMChain(llm=OpenAI(), prompt=prompt_template)
  for i in range(3):
    try:
        result = chain.run(chat_history)
        data = json.loads(result)
        data['appointment_status']="Success"
        data['status_message']="User Appointment has been scheduled successfully."
        appointment_status_entry = leads_and_followup_status(
            hcf_id=hcf_id,
            appointment_status=data.get('appointment_status', ''),
            status_message=data.get('status_message', ''),
            username=data.get('username', ''),
            email_address=data.get('email_address', ''),
            medical_procedures_name=data.get('medical_procedures_name', ''),
            preferred_country=data.get('preferred_country', ''),
            preferred_city=data.get('preferred_city', ''),
            important_concerns=data.get('important_concerns', ''),
            preferred_date=data.get('Preferred_Date', ''),
            summary=data.get('summary', '')
        )
        session.add(appointment_status_entry)
        session.commit()
        session.close()
        return json.dumps(data, indent=4)
    except Exception as e:
        print(e)
        continue

  return json.dumps({
      'appointment_status': "Failure",
      'status_message': "Failed to schedule appointment after 3 attempts, Try Again",
  }, indent=4)

