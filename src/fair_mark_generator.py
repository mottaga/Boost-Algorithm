import itertools 
import operator as op
from functools import reduce


def accuracy(mark_one, mark_two):
    acc = 0
    for i in range(len(mark_one)):
        if mark_one[i] == mark_two[i]:
            acc += 1
    return ((acc/len(mark_one)) * 100)


def maximum_accuracy(marks):
    max_accuracy = 0
    for i in range(len(marks)):
        if marks[i] in [marks[x] for x in range(len(marks)) if x != i]:
            return 100
        for j in range(i+1,len(marks)):
            if max_accuracy < accuracy(marks[i], marks[j]):
                max_accuracy = accuracy(marks[i], marks[j])
    return max_accuracy


def all_marks_generation(generator):
    marks_list = list(itertools.permutations(generator, len(generator)))
    all_marks = []
    for j in range(len(marks_list)):
        temp = ""
        for k in range(len(generator)):
            temp += marks_list[j][k]
        all_marks += [temp]    
    return all_marks


def ncr(n, r):
    r = min(r, n-r)
    numer = reduce(op.mul, range(n, n-r, -1), 1)
    denom = reduce(op.mul, range(1, r+1), 1)
    return numer // denom  # or / in Python 2


def compute_maximum_accuracy(n):
    number_of_bits = ncr(n, n//2)
    if n != 3 and n != 2:
        maximum_accuracy_attainable =  (ncr(n - 2, n//2 - 2) + ncr(n - 2, n//2)) / number_of_bits
    elif n == 3: 
        maximum_accuracy_attainable =  (ncr(n - 2, n//2)) / number_of_bits
    else: 
        maximum_accuracy_attainable = 0

    return maximum_accuracy_attainable*100


def fair_mark_generator(n):
    if n <= 16:
        TF = [True, False]
        all_comb_rep = [p for p in itertools.product(TF, repeat=n)]
        remove_list = []
        for comb in all_comb_rep:
            counter_bool = 0
            for boolean in comb:
                if boolean:
                    counter_bool += 1
            if counter_bool != n//2:
                remove_list += [comb]

        for comb in remove_list:
            all_comb_rep.remove(comb)

        marks = []
        for i in range(n):
            marks += [""]

        for comb in all_comb_rep:
            for i in range(len(comb)):
                if comb[i]:
                    marks[i] += "1"
                else:
                    marks[i] += "0"
    else:
        print('Too much time with n > 16')
        return None

    copy_marks = marks.copy()
    j = 1
    while len(marks[-1]) < 1024:
        for i in range(n):
            marks[i] += copy_marks[(i+j) % n]
        j += 1

    return marks


if __name__ == "__main__":
    n = 5
    marks = fair_mark_generator(n)
    for index, mark in enumerate(marks):
        print(f'Mark {index}: {mark}\n')
    print(f"Marks length: {len(marks[0])}")
    print(f"Marks accuracy: {maximum_accuracy(marks)}")
    print(f"Maximum theoretical accuracy: {compute_maximum_accuracy(n)}")
