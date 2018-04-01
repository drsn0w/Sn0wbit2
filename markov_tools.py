import markovify
import nltext
import os
import random

def regenerate_model(t_fname):
    p_text = open(t_fname).read()
    m_model = markovify.NewlineText(p_text)
    m_json = m_model.chain.to_json()

    m_text = open(t_fname + ".mchain", 'w')
    m_text.write(m_json)
    m_text.close()

def reset_model(t_fname):
    os.remove(t_fname)
    os.remove(t_fname + ".mchain")

def get_starting_words(t_model):
    starting_words = [key for key in t_model.chain.model.keys() if "___BEGIN__" in key]
    only_starting_words = []
    for cur in starting_words:
        only_starting_words.append(cur[1])

    return only_starting_words

def get_random_starting_word(t_model):
    starting_words = get_starting_words(t_model)
    w_index = random.randint(0, len(starting_words)-1)
    return starting_words[w_index]

def botify(sentence):
    return sentence.upper()

def humanize(sentence):
    punctuation = [".", "?", "!", "??", "!?","..."]
    p_index = random.randint(0,len(punctuation)-1)
    return sentence.lower().capitalize() + punctuation[p_index]
