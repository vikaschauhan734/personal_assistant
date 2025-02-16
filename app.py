import os
import smtplib
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase 
from email import encoders 
from langchain_core.tools import StructuredTool, ToolException
from pydantic import BaseModel, Field
import pywhatkit
from langchain.agents import AgentType, initialize_agent
#from langchain_ollama.llms import OllamaLLM
from langchain_groq import ChatGroq
import streamlit as st

# Load environment variables
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY")
smtp_password=os.getenv("SMTP_PASSWORD")
sender=os.getenv("EMAIL_ADDRESS")

# Define Email Tool
class SendEmailInput(BaseModel):
    email_address: str = Field(description="The email address to send the attachment to")
    attachment_name: str = Field(description="The name of the file to send")

def _handle_error(error: ToolException) -> str:
    return f"The following errors occurred during tool execution: `{error.args[0]}`"

def send_email(email_address: str, attachment_name: str) -> str:
    """Send an attachment to a given email address."""
    msg = MIMEMultipart()
    msg['Subject']=f"Sent file {attachment_name}"
    msg['From']=sender
    msg['To']=email_address
    msg.attach(MIMEText(f"Please find the attached file {attachment_name}.","plain"))
    attachment=open(os.path.join("D:/projects/personal_assistant/brochures",attachment_name), "rb")
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment; filename= %s" % attachment_name)
    msg.attach(p) 

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, smtp_password)
        smtp_server.sendmail(sender, email_address, msg.as_string())
    response = f"Sent attachment to {email_address} via Email (Gmail)."
    return response

email_sender = StructuredTool.from_function(func=send_email,
                                            name="email_sender",
                                            description="send email",
                                            args_schema=SendEmailInput,
                                            return_direct=True,
                                            handle_tool_error=_handle_error)

# Define WhatsApp Tool
class SendWhatsAppInput(BaseModel):
    phone_number: str = Field(description="The phone number to send the attachment to")
    attachment_name: str = Field(description="The path of the attachment to send")

def _handle_error(error: ToolException) -> str:
    return f"The following errors occurred during tool execution: `{error.args[0]}`"

def send_whatapp(phone_number: str, attachment_name: str) -> str:
    """Send an image to a given phone number via WhatsApp."""
    pywhatkit.sendwhats_image(phone_number, os.path.join("D:/projects/personal_assistant/brochures",attachment_name), attachment_name)
    response = f"WhatsApp message sent to {phone_number}."
    return response

whatsapp_sender = StructuredTool.from_function(func=send_whatapp,
                                            name="whatsapp_sender",
                                            description="send WhatsApp",
                                            args_schema=SendWhatsAppInput,
                                            return_direct=True,
                                            handle_tool_error=_handle_error)

# Initialize LLM agent
st.title("Personal Assistant")

llm = ChatGroq(model_name="Llama3-8b-8192", temperature=0)
#llm = OllamaLLM(model="deepseek-r1:8b", temperature=0)


input = st.chat_input("How can I help you?")

agent = initialize_agent(tools=[email_sender, whatsapp_sender],
                         llm=llm,
                         agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, # This agent is capable of invoking tools that have multiple inputs.
                         verbose=True)

if input:
    st.write(agent.invoke(input))

