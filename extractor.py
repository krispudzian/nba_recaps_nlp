import spacy
import pyinflect
from spacy.matcher import Matcher
from collections import Counter

from helpers import (
    get_subj_text,
    get_pobjs_text
)

nlp = spacy.load('en_core_web_sm')


def merge_noun_chunks():
    if "merge_noun_chunks" not in nlp.pipe_names:
        nlp.add_pipe("merge_noun_chunks", last=True)
    if "merge_noun_chunks" in nlp.disabled:
        nlp.enable_pipe("merge_noun_chunks")


def get_streaks(text, starts):
    doc = nlp(text)
    sentences = []
    for token in doc:
        if token.lower_ in ["straight", "streak", "consecutive"]:
            if token.sent.start not in starts:
                starts.append(token.sent.start)
                sentences.append(token.sent)

    print("Streaks. Found {} streak(s)".format(len(sentences)))
    return sentences


def get_records(text, starts):
    doc = nlp(text)
    starts.append(0)
    sentences = [doc[0].sent]
    matcher = Matcher(nlp.vocab)
    pattern = [
            [
                {"ORTH": {"IN": ["career", "season", "franchise"]}},
                {"ORTH": "-", "OP": "?"}, 
                {"ORTH": {"IN": ["best", "high", "worst", "low", "record"]}}
            ]
    ]
    matcher.add("records", pattern)
    matches = matcher(doc)
    for match_id, start, end in matches:
        if doc[start].sent.start not in starts:
            sentences.append(doc[start].sent)
            starts.append(doc[start].sent.start)

    print("Records. Found {} record(s)".format(len(sentences)))
    # print(sentences)
    return sentences


def get_filtered_articles(extracted):
    merge_noun_chunks()
    filtered = []
    for art in extracted:
        # print(art[0])
        streak_tokens = get_streak_tokens(art[1])
        text = streak_extractions(streak_tokens)
        filtered.append((art[0], text, art[2]))
    return filtered


def get_streak_tokens(sentences):
    doc = nlp(sentences)

    matcher = Matcher(nlp.vocab)
    pattern = [
        [
            {'TEXT': {'REGEX': 'straight|consecutive|streak'}}
        ]
    ]

    matcher.add("streaks", pattern)
    matches = matcher(doc)

    streak_tokens = [doc[start] for _, start, _ in matches]

    return streak_tokens


def streak_extractions(streak_tokens):
    # print("Total tokens: ", len(streak_tokens))

    filtered_sents = []

    dobjs = [token for token in streak_tokens if token.dep_ in ["dobj", "nsubj"]]
    pobjs = [token for token in streak_tokens if token.dep_ in ["pobj"]]

    for token in pobjs:
        sent = handle_obj(token, True)
        if len(sent) > 0:
            filtered_sents.append(sent)

    for token in dobjs:
        sent = handle_obj(token)
        if len(sent) > 0:
            filtered_sents.append(sent)
    return filtered_sents


def handle_obj(token, is_pobj = False):
    ret_text = ""
    verb = token.head
    if is_pobj == True:
        prep = token.head
        verb = prep.head
        # if prep's head is not a verb, a pattern gets too complicated
        if verb.pos_ != "VERB":
            return ret_text

    # some sentences are complicated and they don't match with any pattern coverd here
    # In this case only the whole sentence will be shown
    if (verb.tag_ not in ["VBD", "VBN"]) and (verb.head.tag_ not in ["VBD", "VBN"]):
        # print(".........Pattern not covered")
        return ret_text

    # get the subject's text
    # Note: It may be an empty string
    subj_text = get_subj_text(verb)
    
    verb_text = verb.text
    # verbs in past tense look more natural
    if verb.tag_ != "VBD":
        verb_text =  verb._.inflect('VBD')

    # add more info if there is a prep child for the token
    right_info = get_pobjs_text(token, verb)

    # array to print the extracted sentence
    print_text = [subj_text, verb_text, token.text, right_info]

    # when token is a subject, we handle it differently
    if token.dep_ == "nsubj":
        print_text = [token.text, verb_text, right_info]
   
    if is_pobj == True:
        dobj_text = ""
        try:
            dobj = [child for child in verb.rights if child.dep_ == "dobj"][0]
            dobj_text = dobj.text
        except IndexError:
            pass
        print_text = [subj_text, verb_text, dobj_text, prep.text, token.text, right_info]
    for word in print_text:
        if len(word) > 0:
            ret_text += word + " "
    # print(*print_text)

    return ret_text
