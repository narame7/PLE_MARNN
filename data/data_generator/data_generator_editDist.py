import numpy as np
from tqdm import tqdm
import json
import os
import sys
import argparse

par = argparse.ArgumentParser()
par.add_argument("-d", "--data_name", default='typo',
                 type=str, help="select a data name (ids/typo)")
args = par.parse_args()
op = "insert"
if args.data_name == "typo":
    op = "replace"

with open("ids_target_vocab.json", "r") as json_file:
    target_vocab = json.load(json_file)

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname('__file__'))))))
os.chdir(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname('__file__'))))))
from util.helpers import apply_fix
data_path = "data/network_inputs/iitk-"+args.data_name+"-1189/"
data = np.load(data_path+'tokenized-examples.npy').item()
train = open(data_path+"data_train_qqqq.txt", 'w')
val = open(data_path+"data_val_qqqq.txt", 'w')

'''
def getEditDistance(a, b):
    la,lb = len(a),len(b)

    d=[[0 for _ in range(int(lb+1))] for _ in range(int(la+1))]
    for i in range(1,la+1): d[i][0]=i
    for i in range(1,lb+1): d[0][i]=i

    for i in range(1,la+1):
      for j in range(1,lb+1):
        d[i][j] = d[i-1][j-1] if a[i-1] == b[j-1] else min(d[i-1][j-1],d[i][j-1],d[i-1][j-1])+1

    return d
'''

def getEditDistance(a, b):
    dist = np.zeros((len(a) + 1, len(b) + 1),dtype=np.int64)
    dist[:, 0] = list(range(len(a) + 1))
    dist[0, :] = list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            insertion = dist[i, j - 1] + 1
            deletion = dist[i - 1, j] + 1
            match = dist[i - 1, j - 1]
            if a[i - 1] != b[j - 1]:
                match += 1  # -- mismatch
            dist[i, j] = min(insertion, deletion, match)
    return dist.tolist()

def getTrace(a, b, dist):
    log = list()
    i, j = len(a),len(b)
    while i != 0 or j != 0:
        s = min(dist[i-1][j], dist[i-1][j-1], dist[i][j-1])
        if s == dist[i][j]:
            i -= 1
            j -= 1
        else:
            if s == dist[i-1][j]:
                log.append(["i", j, a[i-1]])
                i -= 1
            elif s == dist[i][j-1]:
                log.append(["d", j-1])
                j -= 1
            elif s == dist[i-1][j-1]:
                log.append(["r", j-1, a[i-1]])
                i -= 1
                j -= 1
    return log

for k in tqdm(data['train']):
    for i in data['train'][k]:
        #source sequence
        source = i[0]
        lines = source.count('~')
        for l in range(lines):
            if l >= 10:
                source = source.replace(list(str(l))[0] + " " + list(str(l))[1] + " ~ ", "", 1)
            else:
                source = source.replace(str(l) + " ~ ", "", 1)
        source = source.replace("  ", " ")
        source = source.split()
        #target sequence
        if i[1] == '-1':
            target = target = ["0" for i in range(len(source))]
        else:
            fixed = apply_fix(i[0], i[1], op)
            lines = fixed.count('~')
            for l in range(lines):
                if l >= 10:
                    fixed = fixed.replace(list(str(l))[0] + " " + list(str(l))[1] + " ~ ", "", 1)
                else:
                    fixed = fixed.replace(str(l) + " ~ ", "", 1)
            fixed = fixed.replace("  ", " ")
            fixed = fixed.split()

            dist = getEditDistance(fixed, source)
            log = getTrace(fixed, source, dist)
            target = ["0" for i in range(len(source))]
            for l in log:
                if l[0] == "i":
                    target.insert(l[1], target_vocab[l[2]])
                elif l[0] == "r":
                    target[l[1]] = target[l[1]].replace(target[l[1]], target_vocab[l[2]])
                elif l[0] == "d":
                    target[l[1]] = target[l[1]].replace(target[l[1]], "-1")

        train.write("%s\t%s\n" % (" ".join(source), " ".join(target)))

train.close()

for k in tqdm(data['validation']):
    for i in data['validation'][k]:
        #source sequence
        source = i[0]
        lines = source.count('~')
        for l in range(lines):
            if l >= 10:
                source = source.replace(list(str(l))[0] + " " + list(str(l))[1] + " ~ ", "", 1)
            else:
                source = source.replace(str(l) + " ~ ", "", 1)
        source = source.replace("  ", " ")
        source = source.split()
        #target sequence
        if i[1] == '-1':
            target = target = ["0" for i in range(len(source))]
        else:
            fixed = apply_fix(i[0], i[1], op)
            lines = fixed.count('~')
            for l in range(lines):
                if l >= 10:
                    fixed = fixed.replace(list(str(l))[0] + " " + list(str(l))[1] + " ~ ", "", 1)
                else:
                    fixed = fixed.replace(str(l) + " ~ ", "", 1)
            fixed = fixed.replace("  ", " ")
            fixed = fixed.split()

            dist = getEditDistance(fixed, source)
            log = getTrace(fixed, source, dist)
            target = ["0" for i in range(len(source))]
            for l in log:
                if l[0] == "i":
                    target.insert(l[1], target_vocab[l[2]])
                elif l[0] == "r":
                    target[l[1]] = target[l[1]].replace(target[l[1]], target_vocab[l[2]])
                elif l[0] == "d":
                    target[l[1]] = target[l[1]].replace(target[l[1]], "-1")

        val.write("%s\t%s\n" % (" ".join(source), " ".join(target)))

val.close()
