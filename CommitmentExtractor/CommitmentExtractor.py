import sys
import spacy

if sys.version_info >= (3,):
    import queue
else:
    import Queue as queue

class CommitmentExtractor:

    commisive_verbs = []
    words_after_be = []
    special_verbs = ['be', 'like', 'have', 'let', 'need']
    directional_verbs = ['go', 'plan', 'will', 'intend', 'prepare']
    commit_verbs = ['agree', 'promise', 'commit', 'intend', 'guarantee', 'plan']

    def __init__(self):
        sys.stdout.write('Loading SpaCy model...\n')
        self.spacy_model = spacy.load('en_core_web_lg')
        sys.stdout.write('Loaded.\n')

    def __init__(self, spacy_model):
        self.spacy_model = spacy_model

    def __init__(self, spacy_model, commisive_verbs, words_after_be):
        self.spacy_model = spacy_model
        self.commisive_verbs = commisive_verbs
        self.words_after_be = words_after_be

    # Returns a list of sentences and results:
    # -- para_id
    # -- words in the sentence, and if commisive:
    # -- rule
    # -- subject (ids)
    # -- consequent word (id)
    # -- list of ands:
    # ---- id
    # ---- type (subject, consequent, norm, outside)
    # ---- second consequent (if exists)
    def extract(self, para_list):
        para_id = 0
        tokens_list = []
        for para in para_list:
            try:
                para = para.encode('utf-8', 'ignore')
            except:
                pass
            sents = self.spacy_model(para.decode("utf-8", 'ignore'), disable=['ner']).sents
            for tokens in sents:
                tokens_list.append((para_id, tokens))
            para_id += 1

        all_results = []
        for para_id, tokens in tokens_list:
            results = {}
            results['para_id'] = para_id
            results['words'] = ' '.join([token.text for token in tokens])
            token_id_map = {}
            for tidx, token in enumerate(tokens):
                token_id_map[token.idx] = tidx

            # check occurences of the word 'and'
            # find root, MD, and subject
            and_count = []
            root_verb = None
            second_root = None
            for token in tokens:
                if token.text.lower() in ['and', 'or'] and token.dep_ == 'cc':
                    and_count.append(token)
                if token.dep_ == 'ROOT' and token.tag_.startswith('V'):
                    if not root_verb:
                        root_verb = token
                    else:
                        second_root = token
            if not root_verb:
                results['commisive'] = False
                all_results.append(results)
                continue
            MD_verb = None
            second_MD = None
            subj_noun = None
            second_subj = None
            NEGATED = False
            for token in tokens:
                if token.tag_ == 'MD' and token.head == root_verb:
                    MD_verb = token
                if token.tag_ == 'MD' and token.head == second_root:
                    second_MD = token
                if token.dep_ == 'nsubj' and token.head == root_verb:
                    subj_noun = token
                if token.dep_ == 'nsubj' and token.head == second_root:
                    second_subj = token
                if token.dep_ == 'neg' and token.head == root_verb:
                    NEGATED = True

            if not subj_noun:
                results['commisive'] = False
                all_results.append(results)
                continue
            if NEGATED:
                results['commisive'] = False
                all_results.append(results)
                continue

            # find the whole subject
            subj_flags = [subj_noun]
            subj_queue = queue.Queue()
            subj_queue.put(subj_noun)

            while not subj_queue.empty():
                cur = subj_queue.get()
                for t in tokens:
                    if t.head == cur:
                        subj_queue.put(t)
                        subj_flags.append(t)
            subj_texts = [t.text.lower() for t in subj_flags]
            if not ('we' in subj_texts or 'i' in subj_texts):
                results['commisive'] = False
                all_results.append(results)
                continue
            subj_children = [t for t in tokens if t in subj_flags]

            root_verb_text = root_verb.lemma_.lower()
            good = None
            has_be = None
            rule = ''
            # Rule 1: MD + V and V is commisive
            if MD_verb and root_verb.tag_ == 'VB' and root_verb_text not in self.special_verbs and root_verb_text in self.commisive_verbs:
                good = root_verb
                rule = 'Rule 1: MD+V'
            # Rule 1b: MD + be + V and V is commisive
            elif MD_verb and root_verb.tag_ != 'VB' and root_verb_text in self.commisive_verbs:
                for token in tokens:
                    if token.text == 'be' and token.dep_ == 'aux' and token.head == root_verb:
                        good = root_verb
                        rule = 'Rule 1b: MD+be+V'
                        break
            # Rule 1a: MD + be + after_be
            # Rule 2: MD + be able to + V and V is commisive
            elif MD_verb and root_verb_text == 'be':
                prev = None
                has_be = None
                for token in tokens:
                    if prev == root_verb and token.lemma_.lower() in self.words_after_be:
                        good = token
                        rule = 'Rule 1a: MD+be+other'
                        has_be = root_verb
                        break
                    if token.tag_ == 'VB' and token.head.text == 'able' and token.dep_ == 'xcomp' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 2: MD+be+able+to+V'
                        has_be = root_verb
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 2a: MD+be+able+to+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head.text == 'able' and token.dep_ == 'xcomp' and token.lemma_.lower() == 'be':
                        has_be = token
                    prev = token
            # Rule 3: MD + like to + V and V is commisive
            elif MD_verb and root_verb_text == 'like':
                has_be = None
                for token in tokens:
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 3: MD+like+to+V'
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 3a: MD+like+to+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() == 'be':
                        has_be = token
            # Rule 5: MD + let + PRP + V and V is commisive
            elif MD_verb and root_verb_text == 'let':
                has_be = None
                for token in tokens:
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'ccomp' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 5: MD+let+other+V'
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 5a: MD+let+other+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'ccomp' and token.lemma_.lower() == 'be':
                        has_be = token
            # Rule 7: MD + have/other verbs
            elif MD_verb and root_verb_text == 'have':
                good = root_verb
                rule = 'Rule 7: MD+have'
            # Rule 8: be going/planning/willing + TO + V and V is commisive
            elif root_verb.tag_ == 'VBG' and root_verb_text in self.directional_verbs:
                has_be = None
                for token in tokens:
                    # if token.dep_ == 'neg' and token.head == root_verb:
                    #     good = None
                    #     break
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 8: be+going+to+V'
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 8a: be+going+to+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() == 'be':
                        has_be = token
            # Rule 9: look+ forward + to + V and V is commisive
            elif root_verb_text == 'look':
                flags = [t.lemma_.lower() + '_' + t.tag_ + '_' + t.head.lemma_.lower() for t in tokens]
                if 'forward_RB_look' in flags and 'to_IN_look' in flags:
                    fidx = flags.index('to_IN_look')
                    if fidx + 1 < len(tokens):
                        token = tokens[fidx + 1]
                        if token.tag_.startswith(
                                'V') and token.head.text == 'to' and token.lemma_.lower() in self.commisive_verbs:
                            good = token
                            rule = 'Rule 9: look+forward+to+V'
                        if token.tag_.startswith('V') and token.head.text == 'to' and token.lemma_.lower() == 'be':
                            if fidx + 2 < len(tokens):
                                tt = tokens[fidx + 2]
                                if tt.lemma_.lower() in self.words_after_be:
                                    good = tt
                                    rule = 'Rule 9a: look+forward+to+be+other'
            # Rule 10: agree/promise/commit/intend/guarantee/plan + TO + V and V is commisive
            elif root_verb_text in self.commit_verbs:
                has_be = None
                for token in tokens:
                    # if token.dep_ == 'neg' and token.head == root_verb:
                    #     good = None
                    #     break
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 10: agree+to+V'
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 10a: agree+to+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() == 'be':
                        has_be = token
            # Rule 11: take + a/an + vow/oath/pledge +  go+ V and V is commisive
            elif root_verb_text == 'take':
                has_be = None
                for token in tokens:
                    # if token.dep_ == 'neg' and token.head == root_verb:
                    #     good = None
                    #     break
                    if token.tag_ == 'VB' and token.head.lemma_ in ['vow', 'pledge',
                                                                    'oath'] and token.dep_ == 'acl' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 11: take+a+vow+to+V'
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 11a: take+a+vow+to+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head.lemma_ in ['vow', 'pledge',
                                                                    'oath'] and token.dep_ == 'acl' and token.lemma_.lower() == 'be':
                        has_be = token
            # Rule 13: Need+TO+VB
            elif root_verb_text == 'need':
                has_be = None
                for token in tokens:
                    # if token.dep_ == 'neg' and token.head == root_verb:
                    #     good = None
                    #     break
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() in self.commisive_verbs:
                        good = token
                        rule = 'Rule 13: need+to+V'
                        break
                    if has_be:
                        if token.lemma_.lower() in self.words_after_be:
                            good = token
                            rule = 'Rule 13a: need+to+be+other'
                            break
                        has_be = None
                    if token.tag_ == 'VB' and token.head == root_verb and token.dep_ == 'xcomp' and token.lemma_.lower() == 'be':
                        has_be = token
            if not good:
                results['commisive'] = False
                all_results.append(results)
                continue

            results['commisive'] = True
            results['rule'] = rule
            results['subject_id'] = [token_id_map[t.idx] for t in subj_children]
            results['subject'] = ' '.join([t.text for t in subj_children])
            results['commisive_word_id'] = token_id_map[good.idx]
            if 'a' in rule[:rule.index(':')]:
                results['commisive_word'] = 'be ' + good.text
            else:
                results['commisive_word'] = good.text

            if len(and_count) == 0:
                results['compositions'] = []
                all_results.append(results)
                continue

            compositions = []
            for and_token in and_count:
                composition = {}
                composition['composition_word_id'] = token_id_map[and_token.idx]
                composition['composition_word'] = and_token.text
                if and_token in subj_children:
                    composition['composition_type'] = 'Subject'
                    compositions.append(composition)
                    continue

                # the conjunction is in consequents
                has_and = None  # check whether this 'and' conjuncts the root
                has_conj = None # check whether there is a conjuncted verb
                the_one_after = None #
                for token in tokens:
                    if token.tag_.startswith('V') and token.dep_ == 'conj':
                        if has_conj and not the_one_after:
                            the_one_after = token
                        if has_be:
                            if token.head == has_be:
                                has_conj = token
                        else:
                            if token.head == good:
                                has_conj = token
                    if token == and_token:
                        if has_be:
                            if token.head == has_be:
                                has_and = token
                        else:
                            if token.head == good:
                                has_and = token
                if not has_conj:
                    composition['composition_type'] = 'Attribute'
                    compositions.append(composition)
                    continue
                if not has_and:
                    composition['composition_type'] = 'Other'
                else:
                    # check whether or not it has its own subject
                    # check whether it's commisive
                    composition['composition_type'] = 'undecided'
                    if has_conj:
                        for token in tokens:
                            if token.dep_ == 'nsubj' and token.head == has_conj:
                                composition['composition_type'] = 'Outside'
                                break
                    if has_conj.lemma_.lower() not in self.special_verbs and has_conj.lemma_.lower() in self.commisive_verbs:
                        if composition['composition_type'] != 'undecided':
                            composition['composition_type'] = 'Norm'
                        else:
                            composition['composition_type'] = 'Consequent'
                    elif has_conj.lemma_.lower() == 'be' and the_one_after and the_one_after.lemma_.lower() in self.words_after_be:
                        if composition['composition_type'] != 'undecided':
                            composition['composition_type'] = 'Norm'
                        else:
                            composition['composition_type'] = 'Consequent'
                    if composition['composition_type'] == 'undecided':
                        composition['composition_type'] = 'Other'
                # format: tokens, subject, composition, conseq_1, conseq_2
                if composition['composition_type'] in ['Consequent', 'Norm']:
                    if has_conj.lemma_.lower() == 'be':
                        conseq_2 = 'be ' + the_one_after.lemma_.lower()
                        composition['compositioned_commisive_word_id'] = token_id_map[the_one_after.idx]
                    else:
                        conseq_2 = has_conj.lemma_.lower()
                        composition['compositioned_commisive_word_id'] = token_id_map[has_conj.idx]
                    composition['compositioned_commisive_word'] = conseq_2

                compositions.append(composition)
            results['compositions'] = compositions
            all_results.append(results)
        return all_results

def main():
    sys.stdout.write('Loading SpaCy model...\n')
    lg = spacy.load('en_core_web_lg')
    sys.stdout.write('Loaded.\n')

    commisive_verbs = []
    f = open('../words/commisive.txt', 'r')
    for line in f:
        line = line.strip()
        if len(line) > 0:
            commisive_verbs.append(line)
    f.close()

    other_verbs = []
    after_be = []
    f = open('../words/otherverbs.txt', 'r')
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

    ce = CommitmentExtractor(spacy_model=lg, commisive_verbs=commisive_verbs,words_after_be=after_be)
    texts = [u'We will be there on the 9th and I will bring the paperwork.',
             u'I would like to see the quotes and a description of the work to be done.',
             u'Keith and I would like to oversee the bookkeeping.',
             u'I would like to proceed and develop the property.']
    commitments = ce.extract(texts)
    sys.stdout.write('# sentences: {}\n'.format(len(commitments)))
    sys.stdout.write('# commitments: {}\n'.format(len([c for c in commitments if c['commisive']])))

if __name__ == '__main__':
    main()