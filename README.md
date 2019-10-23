# Commitment Extractor
A Python class that extracts commitments from text using a list of rules. 

A commitment is normative relation between a **subject** and an **object** in which the **subject** is committed to bring about 
a **consequent** if the **anticident** holds. The following is an example commitment:

> If you agree to the list, I'll go ahead and submit them.

- **subject**: I
- **object**: you
- **anticident**: you agree to the list
- **consequent**: go ahead and submit them

However, in everyday conversations, the **object** and the **anticident** are frequently ommitted. This class identifies 
the commitment in a sentence, and its **subject** and **consequent** only. 

Note that sometimes people include *compositions* in their commitments. The example above actually includes two consequents:
*go head* and *submit them* (well, whether or not they are actually two separate things is a differnt matter). This class 
also identifies the position of a composition: in the subject, in the consequent, or other places. 

# Requirements
This Python code requires [spacy](https://spacy.io/) and its [models](https://spacy.io/models) to parse texts. We recommend 
the `en_web_core_lg` model. 

# Other
This class checks whether or not a verb phrase is a consequent by checking whether the verb is *commisive*. We have included 
a list of commisive verbs under the `words` folder. Please pay attention to the file path. 

The verb **be** can be either commisive or not commisive. For example:

> I'll be eight tomorrow.

> I'll be there tomorrow.

Whether or not it is commisive depends on the word after it. We have included a list of be phrases under the `words` folder. 
Please check our example code to see how to use it. 

# Example

The following is a sample output. 

```
[{       
        'para_id': 0,
        'words': "If you agree to the list , I 'll go ahead and submit them .",
        'rule': 'Rule 1: MD+V',
        'subject': 'I',
        'subject_id': [7],
        'commisive': True,
        'commisive_word': 'go',
        'commisive_word_id': 9,
        'compositions': [{'composition_type': 'Consequent',
                          'composition_word': 'and',
                          'composition_word_id': 11,
                          'compositioned_commisive_word': 'submit',
                          'compositioned_commisive_word_id': 12}]
},
{
        'para_id': 1, 
        'words': "I 'll be eight tomorrow .", 
        'commisive': False
},
{       
        'para_id': 2,
        'words': "I 'll be there tomorrow .",
        'rule': 'Rule 1a: MD+be+other',
        'subject': 'I',
        'subject_id': [0],
        'commisive': True,
        'commisive_word': 'be there',
        'commisive_word_id': 3,
        'compositions': [],
}]
```
