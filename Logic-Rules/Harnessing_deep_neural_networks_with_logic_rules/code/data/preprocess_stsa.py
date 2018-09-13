# -*- coding: utf8 -*-
import numpy as np
import cPickle
from collections import defaultdict
import sys, re
import pandas as pd
from random import randint
np.random.seed(7294258)

def build_data(data_folder, clean_string=True):
    """
    Loads data
    return:
        resv: [{ y: 0/1,          # 0/1 - 负/正样本
                 text: string,    # 经过 pre-processed 的句子
                 num_words: int,  # 句子单词数量
                 split: 0/1/2     # 0/1/2 - train/dev/test 数据集
              }]
        vocad: { word: count } # 即每个单词出现的次数
    """
    revs = []
    [train_file,dev_file,test_file] = data_folder
    vocab = defaultdict(float)
    with open(train_file, "rb") as f:
        for line in f:
            line = line.strip()
            y = int(line[0])
            rev = []
            rev.append(line[2:].strip())
            if clean_string:
                orig_rev = clean_str(" ".join(rev))
            else:
                orig_rev = " ".join(rev).lower()
            words = set(orig_rev.split())
            for word in words:
                vocab[word] += 1
            datum  = {"y":y,
                      "text": orig_rev,                             
                      "num_words": len(orig_rev.split()),
                      "split": 0} # 0-train, 1-dev, 2-test
            revs.append(datum)
    with open(dev_file, "rb") as f:
        for line in f:       
            line = line.strip()
            y = int(line[0])
            rev = []
            rev.append(line[2:].strip())
            if clean_string:
                orig_rev = clean_str(" ".join(rev))
            else:
                orig_rev = " ".join(rev).lower()
            words = set(orig_rev.split())
            for word in words:
                vocab[word] += 1
            datum  = {"y":y, 
                      "text": orig_rev,                             
                      "num_words": len(orig_rev.split()),
                      "split": 1}
            revs.append(datum)
    with open(test_file, "rb") as f:
        for line in f:       
            line = line.strip()
            y = int(line[0])
            rev = []
            rev.append(line[2:].strip())
            if clean_string:
                orig_rev = clean_str(" ".join(rev))
            else:
                orig_rev = " ".join(rev).lower()
            words = set(orig_rev.split())
            for word in words:
                vocab[word] += 1
            datum  = {"y":y, 
                      "text": orig_rev,                             
                      "num_words": len(orig_rev.split()),
                      "split": 2}
            revs.append(datum)
    return revs, vocab
    
def get_W(word_vecs, k=300):
    """
    Get word matrix. W[i] is the vector for word indexed by i
    return:
        W: shape=(word_size, 300)
        word_idx_map: { word: index }
    """
    vocab_size = len(word_vecs)
    word_idx_map = dict()
    W = np.zeros(shape=(vocab_size+1, k), dtype='float32')            
    W[0] = np.zeros(k, dtype='float32')  # padding word
    i = 1
    for word in word_vecs:
        W[i] = word_vecs[word]
        word_idx_map[word] = i
        i += 1
    return W, word_idx_map

def load_bin_vec(fname, vocab):
    """
    Loads 300x1 word vecs from Google (Mikolov) word2vec
    Only load the vector whose name is in vocab
    return:
        word_vecs: { word: vector }
    """
    word_vecs = {}
    with open(fname, "rb") as f:
        header = f.readline()
        vocab_size, layer1_size = map(int, header.split())
        binary_len = np.dtype('float32').itemsize * layer1_size
        for line in xrange(vocab_size):
            word = []
            while True:
                ch = f.read(1)
                if ch == ' ':
                    word = ''.join(word)
                    break
                if ch != '\n':
                    word.append(ch)   
            if word in vocab:
               word_vecs[word] = np.fromstring(f.read(binary_len), dtype='float32')  
            else:
                f.read(binary_len)
    return word_vecs

def add_unknown_words(word_vecs, vocab, min_df=1, k=300):
    """
    For words that occur in at least min_df documents, create a separate word vector.    
    0.25 is chosen so the unknown vectors have (approximately) same variance as pre-trained ones
    """
    for word in vocab:
        if word not in word_vecs and vocab[word] >= min_df:
            word_vecs[word] = np.random.uniform(-0.25,0.25,k)  

def clean_str(string, TREC=False):
    """
    Tokenization/string cleaning for all datasets except for SST.
    Every dataset is lower cased except for TREC
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)     
    string = re.sub(r"\'s", " \'s", string) 
    string = re.sub(r"\'ve", " \'ve", string) 
    string = re.sub(r"n\'t", " n\'t", string) 
    string = re.sub(r"\'re", " \'re", string) 
    string = re.sub(r"\'d", " \'d", string) 
    string = re.sub(r"\'ll", " \'ll", string) 
    string = re.sub(r",", " , ", string) 
    string = re.sub(r"!", " ! ", string) 
    string = re.sub(r"\(", " \( ", string) 
    string = re.sub(r"\)", " \) ", string) 
    string = re.sub(r"\?", " \? ", string) 
    string = re.sub(r"\s{2,}", " ", string)    
    return string.strip() if TREC else string.strip().lower()

def clean_str_sst(string):
    """
    Tokenization/string cleaning for the SST dataset
    """
    string = re.sub(r"[^A-Za-z0-9(),!?\'\`]", " ", string)   
    string = re.sub(r"\s{2,}", " ", string)    
    return string.strip().lower()

if __name__=="__main__":    
    stsa_path = sys.argv[1]     
    w2v_file = sys.argv[2]
    train_data_file = "%s/stsa.binary.phrases.train" % stsa_path
    dev_data_file = "%s/stsa.binary.dev" % stsa_path
    test_data_file = "%s/stsa.binary.test" % stsa_path
    data_folder = [train_data_file, dev_data_file, test_data_file]    
    print "loading data...",        
    revs, vocab = build_data(data_folder, clean_string=True)
    max_l = np.max(pd.DataFrame(revs)["num_words"])
    print "data loaded!"
    print "number of sentences: " + str(len(revs))
    print "vocab size: " + str(len(vocab))
    print "max sentence length: " + str(max_l)
    print "loading word2vec vectors...",
    w2v = load_bin_vec(w2v_file, vocab)
    print "word2vec loaded!"
    print "num words already in word2vec: " + str(len(w2v))
    add_unknown_words(w2v, vocab)
    W, word_idx_map = get_W(w2v)
    rand_vecs = {}
    add_unknown_words(rand_vecs, vocab)
    W2, _ = get_W(rand_vecs)
    cPickle.dump([revs, W, W2, word_idx_map, vocab], open("./stsa.binary.p", "wb"))
    print "dataset created!"
    
