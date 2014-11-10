import math
import scipy
import libowl
import sys
import random
import numpy

from libowl import *
from scipy.io import *
from random import shuffle
from numpy import reshape

class Layer(object):

    def __init__(self, length):
        self.length = length
        self.bias = libowl.zeros([length, 1])

def trans(x):
    row = len(x)
    col = len(x[0])
    result = []
    for i in xrange(row):
        for j in xrange(col):
            result.append(x[i][j])
    return result

def make_vector(x, y):
    result = []
    for i in xrange(x):
        if (i == y):
            result.append(1)
        else:
            result.append(0)
    return result

def init_network(layers, weights, data, label, minibatch_size = 256, num_minibatches = 235):
    print 'init network'
    num_layers = len(layers)
    for i in xrange(num_layers - 1):
        row = layers[i + 1].length
        col = layers[i].length
        var = math.sqrt(4.0 / (row + col))  # XXX: variance or stddev?
        weights.append(libowl.randn([row, col], 0.0, var))

    loader = scipy.io.loadmat('mnist_all.mat')
    tmp_data = []
    tmp_label = []
    for i in xrange(10):
        key = 'train' + str(i)
        lvector = make_vector(10, i)
        for j in xrange(len(loader[key])):
            tmp_data.append(loader[key][j])
            tmp_label.append(lvector)
    idx = []
    for i in xrange(len(tmp_data)):
        idx.append(i)
    random.shuffle(idx)

    k = 0
    for i in xrange(num_minibatches):
        minibatch_data = []
        minibatch_label = []
        for j in xrange(minibatch_size):
            minibatch_data.append(tmp_data[idx[k]])
            minibatch_label.append(tmp_label[idx[k]])
            k = k + 1
            if k >= len(tmp_data):
                break

        #print len(reshape(minibatch_data, (len(minibatch_data) * len(minibatch_data[0]), 1)))
        data.append(trans(minibatch_data))
        label.append(trans(minibatch_label))
        data.append(reshape(minibatch_data, (len(minibatch_data) * len(minibatch_data[0]), 1)).tolist())
        label.append(reshape(minibatch_label, (len(minibatch_label) * len(minibatch_label[0]), 1)).tolist())

        if k >= len(tmp_data):
            break

def softmax(m):
    maxval = m.max(0)
    centered = m.norm_arithmetic(maxval, libowl.arithmetic.sub)
    class_normalizer = libowl.ln(libowl.exp(centered).sum(0)) + maxval
    return libowl.exp(m.norm_arithmetic(class_normalizer, libowl.arithmetic.sub))

def print_training_accuracy(o, t, minibatch_size):
    predict = o.max_index(0)
    ground_truth = t.max_index(0)
    correct = (predict - ground_truth).count_zero()
    print 'Training error: {}'.format((minibatch_size - correct) * 1.0 / minibatch_size)

def train_network(layers, weights, data, label,
                  num_epochs=100, num_train_samples=60000, minibatch_size=256,
                  num_minibatches=235, eps_w=0.01, eps_b=0.01):
    num_layers = len(layers)
    for i in xrange(num_epochs):
        print "epoch ", i
        for j in xrange(num_minibatches):
            acts = [None] * num_layers
            sens = [None] * num_layers
            acts[0] = make_narray([layers[0].length, len(data[j]) / layers[0].length], data[j])
            # FF
            for k in xrange(1, num_layers):
                acts[k] = weights[k - 1] * acts[k - 1]
                acts[k].norm_arithmetic(layers[k].bias, libowl.arithmetic.add)
                acts[k] = sigmoid(acts[k])
            # Error
            acts[-1] = softmax(acts[-1])
            target = make_narray([10, len(label[j]) / 10], label[j])

            if ((j % 20) == 0):
                print_training_accuracy(acts[-1], target, minibatch_size)

            sens[-1] = acts[-1] - target
            # BP
            for k in reversed(xrange(num_layers - 1)):
                d_act = libowl.mult(acts[k], 1 - acts[k])
                sens[k] = weights[k].trans() * sens[k + 1];
                # This is element-wise.
                sens[k] = libowl.mult(sens[k], d_act)
            # Update bias
            for k in xrange(1, num_layers):
                layers[k].bias -= eps_b * sens[k].sum(1) / minibatch_size
            # Update weight
            for k in xrange(num_layers - 1):
                weights[k] -= eps_w * sens[k + 1] * acts[k].trans() / minibatch_size

if __name__ == '__main__':
    initialize(sys.argv)
    device = create_cpu_device()
    set_device(device)
    layers = [Layer(28 * 28), Layer(256), Layer(10)]
    weights = []
    data = []
    label = []
    init_network(layers, weights, data, label)
    train_network(layers, weights, data, label)
