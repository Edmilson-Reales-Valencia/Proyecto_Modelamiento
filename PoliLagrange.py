def interpolation(x, X, Y):
    y = 0.0
    n = len(X)
    
    for i in range(n):
        L = 1.0
        for j in range(n):
            if j != i:
                L *= (x - X[j]) / (X[i] - X[j])
        y += L * Y[i]
    
    return y