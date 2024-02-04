import math
import random

Tiny = 5.0e-15  # mach. accuracy = 1.0e-19
error_value = -99.9
MaxSize = 65520
MaxSingle = MaxSize // 4  # max element size single array


def rNormal(Mean, StandardDeviation):
    r = 0.0
    v1 = 0.0
    v2 = 0.0
    v3 = 0.0
    dev = 0.0

    if StandardDeviation <= 0:
        return error_value

    while True:
        v1 = 2 * random.random() - 1
        v2 = 2 * random.random() - 1
        r = v1 ** 2 + v2 ** 2

        if r < 1.0:
            break

    if random.random() < 0.5:
        v3 = v2
    else:
        v3 = v1

    dev = v3 * math.sqrt((-2 * math.log(r)) / r)

    return Mean + dev * StandardDeviation


def rLogNormal(GM, GSD):
    if GM < Tiny or GSD <= 1:
        return error_value

    return math.exp(rNormal(math.log(GM), math.log(GSD)))


def rTriangular(Minimum, Maximum, MostLikely):
    if Maximum <= Minimum or MostLikely <= Minimum or MostLikely >= Maximum:
        return error_value

    base = Maximum - Minimum
    part = MostLikely - Minimum
    temp = random.random()

    if temp < (part / base):
        temp = Minimum + math.sqrt(base * part * temp)
    else:
        temp = Maximum - math.sqrt(base * (Maximum - MostLikely) * (1 - temp))

    return temp


def rUniform(Minimum, Maximum):
    if Minimum >= Maximum:
        return error_value

    return Minimum + (Maximum - Minimum) * random.random()


def cdfNormal(y, mean, dev):
    if dev <= 0:
        return error_value

    sd = (y - mean) / dev

    x = sd
    r = math.exp(-x ** 2 / 2) / 2.5066282746
    z = x
    y1 = 1 / (1 + 0.231641900 * abs(x))
    y2 = y1 * y1
    y3 = y2 * y1
    y4 = y3 * y1
    y5 = y4 * y1
    t = 1 - r * (0.319381530 * y1 + 0.356563782 * y2 + 1.781477937 * y3 + 1.821255978 * y4 + 1.330274429 * y5)

    if z > 0:
        return t
    else:
        return 1 - t


def icdfNormal(prob, mean, dev):
    if dev <= 0:
        return error_value

    if prob == 1:
        return 1e500
    if prob == 0:
        return -1e500
    if prob <= 0 or prob >= 1:
        return error_value

    if prob > 0.5: 
        xp = 1-prob
    else:
        xp = prob;
        
    t1 = math.sqrt(math.log(1.0 / (xp*xp)))
    t2 = t1*t1
    t3 = t2*t1
    up = 2.515517 + 0.802853 * t1 + 0.010328 * t2 ** 2
    dn = 1 + 1.432788 * t1 + 0.189269 * t2 + 0.001308 * t3
    xp = t1 - up / dn

    if prob <= 0.5:
        return mean - xp * dev
    else:
        return mean + xp * dev


def cdfLogNormal(x, GM, GSD):
    if x == 0:
        return 0

    if GM < 1 or GSD <= 1 or x <= 0:
        return error_value

    u = math.log(GM)
    std = math.log(GSD)

    return cdfNormal((math.log(x) - u) / std, 0, 1)


def icdfLogNormal(prob, GM, GSD):
    if GM < 1 or GSD <= 1:
        return error_value

    if prob == 0:
        return 0
    if prob == 1:
        return 1e200
    if prob <= 0 or prob >= 1:
        return error_value

    u = math.log(GM)
    std = math.log(GSD)
    n = icdfNormal(prob, 0, 1)

    if u + std * n > 1e4:
        return 1e200
    else:
        return math.exp(u + std * n)


def icdfTriangular(y, A, B, ML):
    if B <= A or ML >= B or ML <= A:
        return error_value

    height = 2 / (B - A)
    left_area = (ML - A) * height / 2
    right_area = (B - ML) * height / 2

    if y < (left_area / (right_area + left_area)):
        return A + math.sqrt(2 * y / (height / (ML - A)))
    else:
        return B - math.sqrt(2 * (y - 1) / (height / (ML - B)))


def cdfTriangular(X, A, B, ML):
    if B <= A or ML >= B or ML <= A:
        return error_value

    height = 2 / (B - A)

    if X < ML:
        return 0.5 * (X - A) * (height / (ML - A)) * (X - A)
    else:
        return 1 - 0.5 * (B - X) * (height / (ML - B)) * (X - B)

    if X < A or X > B:
        return 0


def cdfUniform(X, A, B):
    if A >= B or X < A - Tiny or X > B + Tiny:
        return error_value

    return (X - A) / (B - A)


def icdfUniform(Prob, A, B):
    if A >= B or Prob < 0 or Prob > 1:
        return error_value

    return Prob * (B - A) + A