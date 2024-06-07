from gramformer import Gramformer
import torch
import telebot
import spacy
import os
import concurrent.futures

# Load the spaCy English model
nlp = spacy.load("en_core_web_sm")

def set_seed(seed):
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

set_seed(1212)

gf = Gramformer(models=1, use_gpu=False)  # 1=corrector, 2=detector

# Read the bot token from an environment variable
# bot_token = os.environ.get('BOT_TOKEN')

# if bot_token is None:
#     raise ValueError("Bot token environment variable ('BOT_TOKEN') is not set.")

# Replace 'YOUR_BOT_TOKEN' with the actual API token of your bot
bot_token = "6092786649:AAH3hbNKWEwZ3n7F9kYz1CQ2sVXJ7gFxpu0"
bot = telebot.TeleBot(bot_token)

# Define a handler for the /start command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Send a welcome message with instructions
    bot.reply_to(message, "Welcome to Up to 12 Grammar and Spelling checker Bot! Please send me a message, and I'll check it and send it back to you.")

def grammar_correction(message_text):
    influent_paragraph = message_text
    corrected_paragraph = influent_paragraph  # Initialize with the input text
    mistakes_count = 0
    mistakes = []

    while True:
        if mistakes_count == 5:
            break
        mistakes_count += 1
        influent_sentences = list(nlp(corrected_paragraph).sents)
        influent_sentences = [sentence.text for sentence in influent_sentences]
        print("[Influent sentences]", influent_sentences)

        corrected_paragraph = list(gf.correct(corrected_paragraph, max_candidates=1))[0]
        print("[Corrected paragraph]", corrected_paragraph)

        new_mistakes = []
        for influent_sentence in influent_sentences:
            corrected_sentences = gf.correct(influent_sentence, max_candidates=1)
            print("[Input]", influent_sentence)
            for corrected_sentence in corrected_sentences:
                print("[Correction]", corrected_sentence)
                new_mistakes += gf.get_edits(influent_sentence, corrected_sentence)
                print("[Edits]", new_mistakes)

        # If no new mistakes are found, exit the loop
        if not new_mistakes:
            break

        # Add the new mistakes to the list
        mistakes += new_mistakes

    full_output = "Corrected Paragraph:\n" + corrected_paragraph + "\n\nMistakes:\n"
    for index, (tag, mistake, start, end, correction, corr_start, corr_end) in enumerate(mistakes, start=1):
        full_output += f"{index}. Tag: {tag}\n"
        full_output += f"   Mistake: {mistake} (Position: {start}-{end})\n"
        full_output += f"   Correction: {correction} (Position: {corr_start}-{corr_end})\n"
        full_output += "\n"

    return full_output, mistakes, corrected_paragraph

# Define a handler for text messages
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    received_content = message.text
    # Split the content into lines
    lines = received_content.split('\n')
    
    # Initialize variables to store extracted information
    user_message = ""
    user_id = 0
    chat_id = 0
    original_message_id = 0
    
    # Iterate through the lines to extract information
    for line in lines:
        # Split each line into key and value
        parts = line.split(': ', 1)
    
        # Check if there are at least two parts
        if len(parts) == 2:
            key, value = parts
            # Check the key and assign the value to the corresponding variable
            if key == "User Message":
                user_message = value
            elif key == "User ID":
                user_id = int(value)
            elif key == "Chat ID":
                chat_id = int(value)
            elif key == "Original Message ID":
                original_message_id = int(value)

    full_output, mistakes = grammar_correction(user_message)
    
    if mistakes:
        # Format the data in the same way as received_content
        formatted_content = (
            f"User Message: {user_message}\n"
            f"Original Message ID: {original_message_id}\n"
            f"User ID: {user_id}\n"
            f"Chat ID: {chat_id}\n"
            f"Correction details: {full_output}\n"
        )
        bot.reply_to(message, formatted_content)

# Create a pool of worker threads to handle incoming requests concurrently
executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)

# Start the bot and keep it running in a separate thread
def start_bot():
    bot.polling()

if __name__ == "__main__":
    executor.submit(start_bot)