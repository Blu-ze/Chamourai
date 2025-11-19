def supprimer(l, k):
    if k < 1 or k > len(l):
        raise ValueError("Error")
    else:
        long = len(l)
        while k-1 < long-1:
            l[k-1] = l[k]
            k += 1
        l.pop()
        return l

print(supprimer([1,2,3,4,5], 4))

def new_list(n, x):
    l=[]
    while n>0:
        l.append(x)
        n-=1
    return l

print(new_list(5,2))


def historigramme(s):
    l=[]
    n=1
    while n<257:
        l.append(0)
        n+=1
    for i in s:
        l[ord(i)] = l[ord(i)] + 1
    return l

print(historigramme("AAAAAA"))


print(historigramme(""))
print(historigramme(""))