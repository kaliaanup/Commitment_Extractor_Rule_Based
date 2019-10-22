import sys
import spacy
import pprint

from CommitmentExtractor.CommitmentExtractor import CommitmentExtractor as CE

sys.stdout.write('Loading SpaCy model...\n')
lg = spacy.load('en_core_web_lg')
sys.stdout.write('Loaded.\n')

commisive_verbs = []
f = open('words/commisive.txt', 'r')
for line in f:
    line = line.strip()
    if len(line) > 0:
        commisive_verbs.append(line)
f.close()

other_verbs = []
after_be = []
f = open('words/otherverbs.txt', 'r')
for line in f:
    line = line.strip()
    if len(line) > 0 and not ' ' in line:
        other_verbs.append(line)
    elif line.startswith('be '):
        after_be.append(line[3:])
f.close()
commisive_verbs.extend(other_verbs)
sys.stdout.write('# Commisive verbs: {}\n'.format(len(commisive_verbs)))
sys.stdout.write('# Words after be: {}\n'.format(len(after_be)))

ce = CE(spacy_model=lg, commisive_verbs=commisive_verbs, words_after_be=after_be)
texts = [u'We will be there on the 9th and I will bring the paperwork.',
         u'I would like to see the quotes and a description of the work to be done.',
         u'Keith and I would like to oversee the bookkeeping.',
         u'I would like to proceed and develop the property.']
commitments = ce.extract(texts)
sys.stdout.write('Results: \n')
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(commitments)