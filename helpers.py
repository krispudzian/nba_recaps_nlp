import os
import pickle
import spacy
import json
from spacy.matcher import Matcher

nlp = spacy.load("en_core_web_sm")

def dump_json(final_dict, fname):
    fdir = "json_files"
    fpath = os.path.join(fdir, fname)
    with open(fpath, 'w') as fjson:
        json.dump(final_dict, fjson)

def save_pickle(articles, fname):
    fdir = "pickle_files"
    if not fname.endswith(".pickle"):
        fname += ".pickle"
    fpath = os.path.join(fdir, fname)
    with open(fpath, 'wb') as f:
        pickle.dump(articles, f)


def load_pickle(fname):
    fdir = "pickle_files"
    if not fname.endswith(".pickle"):
        fname += ".pickle"
    fpath = os.path.join(fdir, fname)
    with open(fpath, 'rb') as f:
        articles = pickle.load(f)
    return articles


def get_subj_text(verb):
    """
        parameters: 
            verb - a spacy token

        returns:
            text - a word representing the wanted subject
    """
    subj = None
    text = ""

    # if the verb is not of type VBD or VBN, 
    # there is no immediate dependant of type subject.
    # Instead, we try to find subject in the immediate head
    if verb.tag_ not in ["VBD", "VBN"]:
        verb = verb.head
    
    # if our verb's dep_ == "relcl" the subject will be immediate verb
    if verb.dep_ == "relcl":
        subj = verb.head
        try:
            text = subj.text
        except AttributeError:
            pass
        return text

    try:
        subj = [word for word in verb.lefts if word.dep_ in ["nsubj", "nsubjpass"]][0]
        text = subj.text
    except IndexError:
        pass
    
    return text


def get_prep_pobj_text(preps):
    info = ""
    if len(preps) == 0:
        return info
    for prep in preps:
        try:
            pobj = list(prep.rights)[0]
            info += prep.text + " " + pobj.text + " "
        except IndexError as e:
            print("Somehow this prep doesn't have any child", str(e))

    return info

def get_pobjs_text(token, verb):
    # prep childs for token
    token_preps = [child for child in token.rights if child.dep_ == "prep"]
    # prep childs for parent
    verb_preps = [child for child in verb.rights if (child.dep_ == "prep") and (child.text in ["since", "at", "to", "in", "of", "without"]) and (child != token.head)]
    # all preps
    preps = token_preps + verb_preps

    return get_prep_pobj_text(preps)

def filter_out_upper(text):
    if isinstance(text, list):
        text = " ".join([sent.text for sent in text])
    doc = nlp(text)
    pattern = [
        [
            {"IS_UPPER": True, "IS_SENT_START": True}, 
            {"IS_UPPER": True, "OP": "?"}, 
            {"TEXT": "--"},
            {"TEXT": {"IN": ["—", "-"]}},
        ],
        [
            {"IS_UPPER": True, "IS_SENT_START": True}, 
            {"IS_UPPER": True, "OP": "?"}, 
            {"TEXT": ","}, 
            {"TAG": "NNP"}, 
            {"TEXT": "--"},
            {"TEXT": {"IN": ["—", "-"]}},
        ],
        [
            {"TEXT": "TIP"},
            {"TEXT": "-"},
            {"TEXT": "INS"},
        ],
    ]

    matcher = Matcher(nlp.vocab)
    matcher.add("uppers", pattern)

    sents = [sent for sent in doc.sents]
    new_sents = []
    for sent in sents:
        matches = matcher(sent)
        if len(matches) > 0:
            match_id, start, end = matches[0]
            # print(sent[start:end].text)
            new_sents.append(sent[end:].text)
            continue
        new_sents.append(sent.text)

    text = " ".join([sent for sent in new_sents])

    return text

