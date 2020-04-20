import argparse
import itertools
import random

from processors.processor import Processor
from processors.remote_processor import RemoteProcessor
from utils.experiment import Experiment, ExperimentList
from utils.client import add_client_args
from utils.mapping import Mapping

from utils.jsonable import Vault

from math import factorial as fac

from collections import defaultdict
from functools import lru_cache

from numpy.random import choice as np_choice

def binomial(n, k):
    return fac(n) / (fac(k) * fac(n-k))

def num_multicomb(U, length):
    return binomial(len(U) + length - 1, len(U) - 1)

def length_probability(U, length, minl, maxl):
    """
        This function computes the probability that a uniformly randomly
        sampled experiment with a length in range(minl, maxl) has the given
        length.
    """
    return num_multicomb(U, length) / sum(( num_multicomb(U, i) for i in range(minl, maxl) ))

def sample_multcomb_range(seq, minl, maxl):
    """
        Sample uniformly from the set of all multisets of elements of seq with
        sizes between minl (inclusively) and maxl (exclusively).
    """
    if (maxl - minl) <= 1:
        length = minl
    else:
        w = [ length_probability(seq, i, minl, maxl) for i in range(minl, maxl) ]
        # There are fewer experiments of shorter length. Therefore, we need to make
        # sure that we are less likely to generate shorter experiments.
        length = random.choices(range(minl, maxl), weights=w, k=1)[0]
    return sample_multicomb(seq, length)


@lru_cache(16)
def compute_patterns(num, l):
    """
        Compute all possible patterns of distinct instructions in sequences of
        length l and the number of possible instantiations for each of them.
        example for length 5:
            (0, 1, 2, 3, 3): 10292124500
            (0, 0, 0, 0, 0): 500
            (0, 1, 2, 2, 2): 62125500
            (0, 1, 1, 2, 2): 62125500
            (0, 1, 2, 3, 4): 255244687600
            (0, 0, 1, 1, 1): 249500
            (0, 1, 1, 1, 1): 249500
        Computing these numbers is quite non-trivial.
        It is not just the binomial coefficient of |num| and the number of
        distinct placeholders in this pattern (this would falsely count (A, B, B)
        and (B, A, A) as identical sequences).
        It is also not the number of k-permutations (with k=l) since this would
        count (A, B, C) and (C, B, A) as identical sequences.
        We observe that the order of instructions is only significant among
        placeholders that occur in different numbers.
        This is implemented by starting with the number of k-permutations and
        dividing by the number of permutations for each group of equally often
        occuring placeholders.
        As an example, for the pattern (0, 1, 1, 2, 2), we have one placeholder
        that appears once and two placeholders that appear twice each.
        Therefore we compute the number of instantiations as the number of
        3-permutations over the set of instructions and divide by 1! * 2!.
    """
    placeholders = (i for i in range(l))
    all_patterns = set()
    for tup in itertools.combinations_with_replacement(placeholders, l):
        occurrences = defaultdict(lambda:0)
        for k in tup:
            occurrences[k] += 1
        occs = sorted((v for k, v in occurrences.items()))
        r = []
        for x, o in enumerate(occs):
            for y in range(o):
                r.append(x)
        stup = tuple(r)
        all_patterns.add(stup)

    results = []
    for p in all_patterns:
        num_distinct_placeholders = len(set(p))
        num_kperm = binomial(num, num_distinct_placeholders) * fac(num_distinct_placeholders)

        occurrences = defaultdict(lambda:0)
        for k in p:
            occurrences[k] += 1

        freq_per_group_size = defaultdict(lambda:0)
        for k, v in occurrences.items():
            freq_per_group_size[v] += 1

        divisor = 1

        for k, v in freq_per_group_size.items():
            divisor *= fac(v)

        n = num_kperm // divisor
        results.append((p, n))

    return results

def instantiate_pattern(seq, p):
    """
        Replace the placeholders in p (as produced by produce_patterns()) with
        uniformly randomly selected instructions from seq (without replacement).
    """
    placeholders = set(p)
    mapping = dict()
    args = random.sample(seq, len(placeholders))
    for x, i in enumerate(placeholders):
        mapping[i] = args[x]
    exp = tuple((mapping[i] for i in p))
    return exp


def sample_multicomb(seq, l):
    """
        Sample uniformly from the set of all multisets of elements of seq with
        size l. Multisets are represented as sorted tuples.
    """
    # sample a pattern according to the number of possible instantiations
    pats = compute_patterns(len(seq), l)
    ps = [p for p, n in pats]
    ns = [n for p, n in pats]
    divisor = sum(ns)
    ns = list(map(lambda x: x/divisor, ns))
    draw = np_choice(range(len(ps)), 1, p=ns)[0]
    res_pat = ps[draw]
    # res_pat = random.choices(ps, weights=ns, k=1)[0]
    res = instantiate_pattern(seq, res_pat)
    return tuple(sorted(res))

def sample_experiments(I, minl, maxl, num):
    res = set()
    if maxl <= 2 and len(I) < num:
        num = len(I)
    while len(res) < num:
        res.add(sample_multcomb_range(I, minl, maxl))
    return list(res)

def add_random_experiments(elist, mapping, minlength, maxlength, num):
    proc = Processor.get_default_cls()(mapping)
    arch = proc.get_arch()
    insns = arch.insn_list()
    experiments = sample_experiments(insns, minlength, maxlength, num)
    for iseq in experiments:
        e = elist.create_exp(iseq)
        proc.eval(e)

