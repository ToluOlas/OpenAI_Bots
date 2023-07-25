import os
import openai
from dotenv import load_dotenv
from colorama import Fore, Back, Style

# load values from the .env file if it exists
load_dotenv()

# configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

INSTRUCTIONS = """You are a bot that reads emails, and return the most appropriate catergories
An email can have one to two catergories: A Primary Category and a Secondary Catergory
Every email must be assigned a Primary Category.
A Secondary Category is NOT always applicable.

Primary Categories: Package Tracking, Customs & Clearance, Billing, Pickup, Rating & Transit Times, Account & Sales Support, POD proof of delivery, Claims, Supplies, IT Support, Other
Secondary Categories: Paperwork Request, Exception

Do NOT use any other categories other than the ones that are listed.
If a secondary catergory does not fit the email, mark the secindary category as "N/A".
An email can have only one primary category, and 0-1 secondary categories.

Output your answer in this format:"Primary: [INSERT PRIMARY CATEGORY] | Secondary: [INSERT SECONDARY CATEGORY]"

Primary categories CANNOT be used for [INSERT SECONDARY CATEGORY].
Secondary categories CANNOT be used for [INSERT PRIMARY CATEGORY].
For example: "Primary: Package Tracking | Secondary: Exception" is VALID.  "Primary: Paperwork Request | Secondary: Exception" is INVALID. "Primary: Billing | Secondary: Package Tracking" is INVALID. "Primary: Other | Secondary: Paperwork Request" is VALID.

Examples:

Input: The parcel 784573749880 has been stuck in delivery with the following message since 15th March 2020:  "Clearance delay – Import Clearance instructions from the importer are required."  Please can someone let us know what is required so we can get this delivered as soon as possible?
Bot: Primary: Package Tracking | Secondary: N/A

Input: Hello,  I hope you're well. I'm trying to reach out on the phone but no one is picking up. I am urgently waiting to receive my package, it's been stuck in Paris since Tuesday and I'm wondering what's going on? If you could advise us on this as soon as possible, that would be great!  Thank you.
Bot: Primary: Custom & Clearance | Secondary: N/A

Input: We have been charged an extra 9 Euro when the measurements do not exceed what is this for?
Bot: Primary: Billing | Secondary: N/A

Input: I need quotes to send some boxes to very national desintations.
Bot: Primary: Rating & Transit Times | Secondary: N/A

Input: I was charged more that my shipping cost and didnt get my receipt.
Bot: Primary: Other | Secondary: N/A

Input: Please confirm that the shipment will be collected today from our warehouse.
Bot: Primary: Pickup | Secondary: N/A

Input: I would like to delete my account with FedEx so as to stop you making unauthorised charges. Please tell me how to delete my FedEx account.
Bot: Primary: Account & Sales Support | Secondary: N/A

Input: Please send me the hard copy proof of delivery for the below shipments.
Bot: Primary: POD proof of delivery | Secondary: N/A

Input: This says my Parcel was delivered, but I don't have it. It says it was left outside the front door on March 15th at 12:35 we both work from home full time and were home at that time. Who have you left my package with?
Bot: Primary: Claims | Secondary: N/A

Input: Hi, This reply is extremely unhelpful and simply redirects to redelivery, which I specifically previously said was unsuccessful. Please tell your delivery driver to deliver my order to the concierge, or to actually bother to dial the number to deliver the item on the buzzer. Thanks.
Bot: Primary: Supplies | Secondary: N/A

Input: We need to request some more stationery please can you send us.
Bot: Primary: Supplies | Secondary: N/A

Input: I received a response form the Other email address which suggested I try phoning the IT Helpdesk on 01827 711611 
Bot: Primary: IT Support | Secondary: N/A

Input: Good afternoon, Could you please help me with my request could you please forward me a copy of the C88 SAD for this consignment, Collection address: Schaltbau Machine Electrics Ltd, 335-336 Woodside Way, Springvale Industrial Estate, Woodside Way, Cwmbran. NP44 5BR. UK. Delivery address: Asseco CEIT, a. s. Rosina 928 Rosina 013 22 SLOVAKIA Thank you
Bot: Primary: Customs & Clearance | Secondary: Paperwork Request

Input: Hi, Could you provide export docs for consignment 326587198, as soon as they are available, please? Booked on account 002424788 Thanks
Bot: Primary: Customs & Clearance | Secondary: Paperwork Request

Input: ensure that this package will be picked up tomorrow it was due to be picked up from us today driver never arrived
Bot: Primary: Pickup | Secondary: Exception"""

TEMPERATURE = 0.5
MAX_TOKENS = 500
FREQUENCY_PENALTY = 0.2
PRESENCE_PENALTY = 0.6
# limits how many questions we include in the prompt
MAX_CONTEXT_QUESTIONS = 10


def get_response(instructions, previous_questions_and_answers, new_question):
    """Get a response from ChatCompletion

    Args:
        instructions: The instructions for the chat bot - this determines how it will behave
        previous_questions_and_answers: Chat history
        new_question: The new question to ask the bot

    Returns:
        The response text
    """
    # build the messages
    messages = [
        { "role": "system", "content": instructions },
    ]
    # add the previous questions and answers
    for question, answer in previous_questions_and_answers[-MAX_CONTEXT_QUESTIONS:]:
        messages.append({ "role": "user", "content": question })
        messages.append({ "role": "assistant", "content": answer })
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
    # keep track of previous questions and answers
    previous_questions_and_answers = []
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
        response = get_response(INSTRUCTIONS, previous_questions_and_answers, new_question)

        # add the new question and answer to the list of previous questions and answers
        previous_questions_and_answers.append((new_question, response))

        # print the response
        print(Fore.CYAN + Style.BRIGHT + "BOT: " + Style.NORMAL + response)


if __name__ == "__main__":
    main()
