def Q(Q_last, H1, H1t, H2, H2t, Z1, Z2, b, L, n, delta_t=30, c=1.49):
    g = 32.2
    y1t = H1t - Z1
    y2t = H2t - Z2
    y1 = H1 - Z1
    y2 = H2 - Z2
    A_2 = y2 * b
    A_1 = y1 * b

    y_bar = (y1 + y2)/2.
    y_bart = (y1t + y2t)/2.
    A_bar = y_bar*b
    A_bart = y_bart*b
    U = Q_last/A_bar
    R_bar = b*y_bar/(b + 2*y_bar)
    
    Q_intertia = 2*U*(A_bar - A_bart) + U**2*(A_2 - A_1)/L*delta_t
    Q_press = -g*A_bar*(H2 - H1)/L*delta_t
    Q_friction = g *((n/c)**2)*abs(U)*delta_t/R_bar**(4./3.)

    return (Q_last + Q_intertia + Q_press)/(1+Q_friction)

def H(H_t, Qin_t, Qout_t, Qin_new, Qout_new, delta_t, h1_last, h2_last, Z1, Z2, L):
    w1 = 2.
    w2 = 2. 
    As = (w1 + w2)/2 *(L/2.)
    return H_t + (delta_t * 0.5 * (Qin_t - Qout_t + Qin_new - Qout_new))/As

Q_0 = 0
H1 = 2.01
H1t = 2.01
H2 = 1.
H2t = 1.
Z1 = 2.
Z2 = 1.
b = 2.
L = 400.
n = 0.01
theta = 0.5 

for i in range(8):
    q_new = Q(Q_0, H1, H1t, H2, H2t, Z1, Z2, b, L, n)
    q_new_weighted = (1 - theta) * Q_0 + theta * q_new
    print q_new_weighted
    h_new_j1 = H(H1t, 0.17, 0, 0.27, q_new_weighted, 30., H1, H2, Z1, Z2, L)
    h_new_weighted_j1 = (1 - theta) * H1 + theta * h_new_j1
    print h_new_weighted_j1
    h_new_j2 = H(H2t, 0, 0, q_new_weighted, 0, 30., H1, H2, Z1, Z2, L)
    h_new_weighted_j2 = (1 - theta) * H2 + theta * h_new_j2
    print h_new_weighted_j2
    H1 = h_new_weighted_j1
    H2 = h_new_weighted_j2
    Q_0 = q_new_weighted
