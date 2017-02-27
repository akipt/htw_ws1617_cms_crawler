# SOURCE: https://rosettacode.org/wiki/Parsing/Shunting-yard_algorithm#Python

from collections import namedtuple
from pprint import pprint as pp
import sys, getopt

class ShYard:
    OpInfo = namedtuple('OpInfo', 'prec assoc')
    L, R = 'Left Right'.split()

    ops = {
     'NOT': OpInfo(prec=4, assoc=R),
     'AND': OpInfo(prec=3, assoc=L),
     'OR': OpInfo(prec=2, assoc=L),
     '(': OpInfo(prec=9, assoc=L),
     ')': OpInfo(prec=0, assoc=L),
     }

    NUM, LPAREN, RPAREN = 'NUMBER ( )'.split()

    @staticmethod
    def get_postfix(query):
        search_term = query
        infix3 = search_term.replace('(', ' ( ')
        infix3 = infix3.replace(')', ' ) ')
        return ShYard.shunting(ShYard.get_input(infix3))[-1][2]

    @staticmethod
    def get_input(inp=None):
        'Inputs an expression and returns list of (TOKENTYPE, tokenvalue)'

        if inp is None:
            inp = input('expression: ')
        tokens = inp.strip().split()
        tokenvals = []
        for token in tokens:
            if token in ShYard.ops:
                tokenvals.append((token, ShYard.ops[token]))
            # elif token in (LPAREN, RPAREN):
            #    tokenvals.append((token, token))
            else:
                tokenvals.append((ShYard.NUM, token))
        return tokenvals

    @staticmethod
    def shunting(tokenvals):
        outq, stack = [], []
        table = ['TOKEN,ACTION,RPN OUTPUT,OP STACK,NOTES'.split(',')]
        for token, val in tokenvals:
            note = action = ''
            if token is ShYard.NUM:
                action = 'Add number to output'
                outq.append(val)
                table.append((val, action, ' '.join(outq), ' '.join(s[0] for s in stack), note))
            elif token in ShYard.ops:
                t1, (p1, a1) = token, val
                v = t1
                note = 'Pop ops from stack to output'
                while stack:
                    t2, (p2, a2) = stack[-1]
                    if (a1 == ShYard.L and p1 <= p2) or (a1 == ShYard.R and p1 < p2):
                        if t1 != ShYard.RPAREN:
                            if t2 != ShYard.LPAREN:
                                stack.pop()
                                action = '(Pop op)'
                                outq.append(t2)
                            else:
                                break
                        else:
                            if t2 != ShYard.LPAREN:
                                stack.pop()
                                action = '(Pop op)'
                                outq.append(t2)
                            else:
                                stack.pop()
                                action = '(Pop & discard "(")'
                                table.append((v, action, ' '.join(outq), ' '.join(s[0] for s in stack), note))
                                break
                        table.append((v, action, ' '.join(outq), ' '.join(s[0] for s in stack), note))
                        v = note = ''
                    else:
                        note = ''
                        break
                    note = ''
                note = ''
                if t1 != ShYard.RPAREN:
                    stack.append((token, val))
                    action = 'Push op token to stack'
                else:
                    action = 'Discard ")"'
                table.append((v, action, ' '.join(outq), ' '.join(s[0] for s in stack), note))
        note = 'Drain stack to output'
        while stack:
            v = ''
            t2, (p2, a2) = stack[-1]
            action = '(Pop op)'
            stack.pop()
            outq.append(t2)
            table.append((v, action, ' '.join(outq), ' '.join(s[0] for s in stack), note))
            v = note = ''
        return table


if __name__ == '__main__':
    pf = ShYard.get_postfix(sys.argv[1])
    print(pf)
