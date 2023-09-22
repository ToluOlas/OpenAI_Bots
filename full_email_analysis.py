import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Back, Style
#Note: this version does not track context.
# load values from the .env file if it exists
load_dotenv()

# configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

#PROMPT for primary category
PRIMARY_INSTRUCTIONS = """You are a bot that reads emails, and return the most appropriate catergory.
You will be given an email, and must choose a category that is the most fitting for the text.
An email MUST have one category.

The possible categories are: Package Tracking, Customs & Clearance, Billing, Pickup, Rating & Transit Times, Account & Sales Support, POD proof of delivery, Claims, Supplies, IT Support, Other

Do NOT use any other categories other than the ones that are listed.
Ouput in this format: [INSERT CATEGORY]
Do not add any other text that isn't the chosen category.

EXAMPLES:

Input: The parcel 784573749880 has been stuck in delivery with the following message since 15th March 2020:  "Clearance delay – Import Clearance instructions from the importer are required."  Please can someone let us know what is required so we can get this delivered as soon as possible?
Bot: Package Tracking

Input: Hello,  I hope you're well. I'm trying to reach out on the phone but no one is picking up. I am urgently waiting to receive my package, it's been stuck in Paris since Tuesday and I'm wondering what's going on? If you could advise us on this as soon as possible, that would be great!  Thank you.
Bot: Custom & Clearance

Input: We have been charged an extra 9 Euro when the measurements do not exceed what is this for?
Bot: Billing

Input: I need quotes to send some boxes to very national desintations.
Bot: Rating & Transit Times

Input: I was charged more that my shipping cost and didnt get my receipt.
Bot: Other

Input: Please confirm that the shipment will be collected today from our warehouse.
Bot: Pickup

Input: I would like to delete my account with FedEx so as to stop you making unauthorised charges. Please tell me how to delete my FedEx account.
Bot: Account & Sales Support

Input: Please send me the hard copy proof of delivery for the below shipments.
Bot: POD Proof of Delivery

Input: This says my Parcel was delivered, but I don't have it. It says it was left outside the front door on March 15th at 12:35 we both work from home full time and were home at that time. Who have you left my package with?
Bot: Claims

Input: We need to request some more stationery please can you send us.
Bot: Supplies

Input: I received a response form the Other email address which suggested I try phoning the IT Helpdesk on 01827 711611 
Bot: IT Support

Input: Good afternoon, Could you please help me with my request could you please forward me a copy of the C88 SAD for this consignment, Collection address: Schaltbau Machine Electrics Ltd, 335-336 Woodside Way, Springvale Industrial Estate, Woodside Way, Cwmbran. NP44 5BR. UK. Delivery address: Asseco CEIT, a. s. Rosina 928 Rosina 013 22 SLOVAKIA Thank you
Bot: Custom & Clearance

Input: Hi, Could you provide export docs for consignment 326587198, as soon as they are available, please? Booked on account 002424788 Thanks
Bot: Custom & Clearance

Input: ensure that this package will be picked up tomorrow it was due to be picked up from us today driver never arrived
Bot: Pickup

Input: Hi I have received and SMS asking me to pay a charge whoever it is for a parcel i never received. I have even got  a refund back from the company in question. Please advise why i am still being charged this. Thanks
Bot: Claims"""

#PROMPT for secondary category
SECONDARY_INSTRUCTIONS = """You are a bot that reads emails, and return the most appropriate catergory.
You will be given an email, and must choose a category that is the most fitting for the text.
A category is NOT always applicable.

The possible categories are: Paperwork Request, Exception
Paperwork Request = Any email requesting documents like invoices etc.
Exception = Regarding errors or cancellations

Do NOT use any other categories other than the ones that are listed.
Ouput in this format: [INSERT CATEGORY]
Do not add any other text that isn't the chosen category.
If a catergory does not fit the email, mark the category as "N/A".

EXAMPLES:

Input: The parcel 784573749880 has been stuck in delivery with the following message since 15th March 2020:  "Clearance delay – Import Clearance instructions from the importer are required."  Please can someone let us know what is required so we can get this delivered as soon as possible?
Bot: N/A

Input: Hello,  I hope you're well. I'm trying to reach out on the phone but no one is picking up. I am urgently waiting to receive my package, it's been stuck in Paris since Tuesday and I'm wondering what's going on? If you could advise us on this as soon as possible, that would be great!  Thank you.
Bot: N/A

Input: We have been charged an extra 9 Euro when the measurements do not exceed what is this for?
Bot: N/A

Input: I need quotes to send some boxes to very national desintations.
Bot: N/A

Input: I was charged more that my shipping cost and didnt get my receipt.
Bot: N/A

Input: I need an invoice for the package delivered
Bot: Paperwork Request

Input: I would like to delete my account with FedEx so as to stop you making unauthorised charges. Please tell me how to delete my FedEx account.
Bot: N/A

Input: Please send me the hard copy proof of delivery for the below shipments.
Bot: N/A

Input: This says my Parcel was delivered, but I don't have it. It says it was left outside the front door on March 15th at 12:35 we both work from home full time and were home at that time. Who have you left my package with?
Bot: N/A

Input: Hi, This reply is extremely unhelpful and simply redirects to redelivery, which I specifically previously said was unsuccessful. Please tell your delivery driver to deliver my order to the concierge, or to actually bother to dial the number to deliver the item on the buzzer. Thanks.
Bot: N/A

Input: We need to request some more stationery please can you send us.
Bot: N/A

Input: I received a response form the Other email address which suggested I try phoning the IT Helpdesk on 01827 711611 
Bot: N/A

Input: Good afternoon, Could you please help me with my request could you please forward me a copy of the C88 SAD for this consignment, Collection address: Schaltbau Machine Electrics Ltd, 335-336 Woodside Way, Springvale Industrial Estate, Woodside Way, Cwmbran. NP44 5BR. UK. Delivery address: Asseco CEIT, a. s. Rosina 928 Rosina 013 22 SLOVAKIA Thank you
Bot: Paperwork Request

Input: Hi, Could you provide export docs for consignment 326587198, as soon as they are available, please? Booked on account 002424788 Thanks
Bot: Paperwork Request

Input: ensure that this package will be picked up tomorrow it was due to be picked up from us today driver never arrived
Bot: Exception

Input: Good Morning TNT, Please can you send through the export documents for AWB 318682308 we require this to send to HMRC for submission Thanks
Bot: Paperwork Request

Input: There was a mistake to the booking there are three pieces not 1 can you change this?
Bot: Exception

Input: Good morning, Are you able to cancel this booking of your system please. Kind Regards
Bot: Exception

Input: we still receiving bills via e-mail for our account We are a paperless office and we have no system to integrate paper bills into our accounts 
Bot: N/A

Input: Hello  we are Heraeus Noblelight Ltd., Neston UK and are looking for a quotation for a consignment from UK to Co Mayo in Ireland.   This is an oversized consignment 405 cm x 15 cm x 28 cm in a wooden box - gross weight 42 KG.   Can you please advise your site address so that I can check the price and services available.
Bot: N/A

Input: I see that the collection has not been made
Bot: Exception"""

#PROMPT for email analysis
ANALYSIS_INSTRUCTIONS = """You are a bot that reads messages and summaries them.
You will receive an input
You give a short summary on what the message is about, read the tone and come up with a response email.
You can also rate the importance/priority of this message.

Examples:

Input: Hi, Could you send me a statement of account and a copy of all open invoices for this account 002638851 as a matter of urgency. We have been billed to this account in the past, but we should not be. All shipments are booked under account 54451 and that is the account we should be billed under. But if you send me these invoices I will deal with them as a matter of urgency and then you can close account 002638851 Many thanks

Bot: 

The sender is requesting a statement of account and a copy of all open invoices for account 002638851. They believe they have been billed incorrectly under this account and want to address the issue urgently.

Priority: High
Tone: Neutral

Potential Response:

Hi,

Thank you for reaching out to us. I understand that you have been billed incorrectly under account 002638851 and would like to address this matter urgently. I apologize for any inconvenience this may have caused.

I will forward your request to the appropriate department so they can provide you with the statement of account and copies of the open invoices for account 002638851. They will investigate the issue and work towards resolving it as soon as possible.

Input: My package was due from Canada yesterday, Monday 22 March, before 12, delivered to UK. Tracking shows it has been in Indiapoĺis since Friday. Where is it and What's going on?

Bot: 

The sender's package was expected to be delivered from Canada to the UK on Monday 22 March before 12 PM, however, tracking reveals that the package is currently in Indianapolis. They are asking what is the current status of the package and why it has not been delivered yet.

Priority: High 
Tone: Urgent 

Potential Response:

Hi,

Thank you for bringing this matter to our attention. We understand that your package should have been delivered from Canada to the UK on Monday 22 March before 12 PM, however, tracking indicates that it is currently in Indianapolis. We apologize for any inconvenience this may have caused.

We take the timely delivery of your package seriously, and we will investigate the issue right away. We will do our best to ensure that your package is delivered as soon as possible.

Please do not hesitate to contact us if you have any other concerns. We are here to help.

Input: Good afternoon Please can you update me as to the status of the above shipment as according to your scans this is still in Dartford? Many thanks

Bot: 

The sender is asking for an update on the status of their shipment, which according to the scans is still in Dartford. 

Priority: Medium 
Tone: Neutral 

Potential Response:

Hi,

Thank you for bringing this matter to our attention. We understand that you are inquiring about the status of your shipment, which according to the scans is still in Dartford. We apologize for any delays this may have caused.

We will investigate the matter and provide you with an update as soon as possible.

If you have any other concerns, please do not hesitate to contact us. We are here to help."""

TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0.2
PRESENCE_PENALTY = 0.6

def get_response(instructions, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        { "role": "system", "content": instructions },
    ]
    # add the new question
    messages.append({ "role": "user", "content": new_question })

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS,
        top_p=1,
        frequency_penalty=FREQUENCY_PENALTY,
        presence_penalty=PRESENCE_PENALTY,
    )
    return completion.choices[0].message.content


def get_moderation(question):
    """
    Check the question is safe to ask the model

    Parameters:
        question (str): The question to check

    Returns a list of errors if the question is not safe, otherwise returns None
    """

    errors = {
        "hate": "Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.",
        "hate/threatening": "Hateful content that also includes violence or serious harm towards the targeted group.",
        "self-harm": "Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.",
        "sexual": "Content meant to arouse sexual excitement, such as the description of sexual activity, or that promotes sexual services (excluding sex education and wellness).",
        "sexual/minors": "Sexual content that includes an individual who is under 18 years old.",
        "violence": "Content that promotes or glorifies violence or celebrates the suffering or humiliation of others.",
        "violence/graphic": "Violent content that depicts death, violence, or serious physical injury in extreme graphic detail.",
    }
    response = openai.Moderation.create(input=question)
    if response.results[0].flagged:
        # get the categories that are flagged and generate a message
        result = [
            error
            for category, error in errors.items()
            if response.results[0].categories[category]
        ]
        return result
    return None


def main():
    os.system("cls" if os.name == "nt" else "clear")
    # Introduction text
    print(Fore.CYAN + Style.BRIGHT + "Bot is now running...")
    while True:
        # ask the user for their question
        new_question = input(
            Fore.GREEN + Style.BRIGHT + "Enter email here: " + Style.RESET_ALL
        )
        # check the question is safe
        errors = get_moderation(new_question)
        if errors:
            print(
                Fore.RED
                + Style.BRIGHT
                + "Sorry, you're question didn't pass the moderation check:"
            )
            for error in errors:
                print(error)
            print(Style.RESET_ALL)
            continue
        primary_category = get_response(PRIMARY_INSTRUCTIONS, new_question)
        secondary_category = get_response(SECONDARY_INSTRUCTIONS, new_question)
        get_analysis = get_response(ANALYSIS_INSTRUCTIONS, new_question)

        # print the response
        print(Fore.CYAN + Style.BRIGHT + "Primary Category: " + Style.NORMAL + primary_category + " | "
              + Style.BRIGHT + "Secondary Category: " + Style.NORMAL + secondary_category)
        print("")
        print(Fore.CYAN + Style.BRIGHT + "Summary: " + Style.NORMAL + get_analysis)

if __name__ == "__main__":
    main()
