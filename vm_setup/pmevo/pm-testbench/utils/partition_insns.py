from collections import defaultdict
import itertools
import sys

from utils.architecture import Architecture
from utils.experiment import ExperimentList
from utils.mapping import Mapping3

def create_partition(elems, equiv_map):
    """ Partition a collection of elements into buckets of equivalent elements.
        Two elements e1, e2 are considered equivalent if and only if
        equiv_map[(e1, e2)] == True.
        Returns the list of buckets and a mapping of elements to buckets.
    """
    elem_to_bucket = { i: {i} for i in elems }
    for (i1, i2), equiv in equiv_map.items():
        if equiv:
            bucket_i1 = elem_to_bucket[i1]
            bucket_i2 = elem_to_bucket[i2]
            new_bucket = bucket_i1.union(bucket_i2)
            for i in new_bucket:
                elem_to_bucket[i] = new_bucket
    buckets = []
    covered_elems = []
    for i, b in elem_to_bucket.items():
        if i in covered_elems:
            continue
        covered_elems += b
        buckets.append(list(b))
    return buckets, elem_to_bucket


def partition_instructions(elist, singleton_elist, epsilon, verbose=False, stats=None):
    def equals(a, b):
        return 2 * abs(a - b) <= epsilon  * (a + b)

    arch = elist.arch
    insns = arch.insn_list()

    singleton_results = dict()
    for e in singleton_elist:
        assert len(e.iseq) == 1
        i = e.iseq[0]
        t = e.get_cycles()
        singleton_results[i] = t

    singleton_equiv_map = { (i, j): equals(singleton_results[i], singleton_results[j]) for (i, j) in itertools.combinations(insns, 2) }

    insn_buckets, insn_to_bucket = create_partition(insns, singleton_equiv_map)

    complex_exps = defaultdict(lambda: defaultdict(list))
    for e in elist:
        insn_set = set(e.iseq)
        assert len(insn_set) == 2
        i, j = insn_set
        complex_exps[i][j].append(e)
        complex_exps[j][i].append(e)

    num_differing_exps = 0
    num_differing_distinguishing_exps = 0

    def check_equivalent_complex(i1, i2):
        nonlocal num_differing_exps, num_differing_distinguishing_exps
        i1_exps = complex_exps[i1]
        i2_exps = complex_exps[i2]
        for i in insns:
            if i == i1 or i == i2:
                continue
            i1i_exps = sorted(i1_exps[i], key = lambda x: len(x.iseq))
            i2i_exps = sorted(i2_exps[i], key = lambda x: len(x.iseq))
            for e1, e2 in zip(i1i_exps, i2i_exps):
                if not (len(e1.iseq) == len(e2.iseq)):
                    num_differing_exps += 1
                    if verbose:
                        print("Warning: Corresponding experiments with differing length!", file=sys.stderr)
                        print("  {}".format(repr(e1)), file=sys.stderr)
                        print("  {}".format(repr(e2)), file=sys.stderr)
                    return False
                assert len(e1.iseq) == len(e2.iseq)
                if not equals(e1.get_cycles(), e2.get_cycles()):
                    if not (len(e1.iseq) == len(e2.iseq)):
                        num_differing_distinguishing_exps += 1
                    if verbose:
                        print("distinguishing experiments for {} and {}:".format(i1, i2))
                        print("  {}".format(repr(e1)))
                        print("  {}\n".format(repr(e2)))
                    return False
        return True

    equality_map = dict()
    for bucket in insn_buckets:
        for i1, i2 in itertools.combinations(bucket, 2):
            equality_map[(i1, i2)] = check_equivalent_complex(i1, i2)

    final_buckets, insn_to_final_bucket = create_partition(insns, equality_map)

    if stats is not None:
        stats["num_differing_exps"] = num_differing_exps
        stats["num_differing_distinguishing_exps"] = num_differing_distinguishing_exps

    return final_buckets, insn_to_final_bucket

def compute_representatives(elist, singleton_elist, epsilon):
    representatives = []
    insn_to_representative = dict()

    buckets, insn_to_bucket = partition_instructions(elist, singleton_elist, epsilon)

    for b in buckets:
        sorted_bucket = sorted(b, key=lambda x: x.name)
        representative = sorted_bucket[0]
        representatives.append(representative)
        for i in b:
            insn_to_representative[i] = representative

    return representatives, insn_to_representative


def restrict_elist(elist, insn_representatives):
    arch = elist.arch
    new_arch = Architecture()
    new_arch.ports = arch.ports
    whitelist = insn_representatives
    new_arch.insns = { n: i for n, i in arch.insns.items() if i in whitelist }

    new_elist = ExperimentList(new_arch)
    for e in elist:
        new_iseq = []
        for i in e.iseq:
            if i not in whitelist:
                new_iseq = None
                break
            new_iseq.append(i)
        if new_iseq is None:
            continue
        new_exp = new_elist.create_exp(new_iseq)
        new_exp.result = e.result
        new_exp.other_results = e.other_results

    return new_elist

def generalize_mapping(old_arch, mapping, insn_to_representative):
    assert isinstance(mapping, Mapping3)
    new_mapping = Mapping3(old_arch)
    insns = old_arch.insn_list()
    for i in insns:
        representative = insn_to_representative[i]
        new_mapping.assignment[i] = mapping.assignment[representative][:]
    return new_mapping


