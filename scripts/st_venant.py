def Q(Q_last, H1, H2, Z1, Z2, b, L, n, delta_t=30, c=1.49):
    g = 32.2
    y1 = H1 - Z1
    y2 = H2 - Z2
    A_2 = y2 * b
    A_1 = y1 * b

    y_bar = (y1 + y2)/2.
    A_bar = y_bar*b
    U = Q_last/A_bar
    R_bar = b*y_bar/(b + 2*y_bar)
    
    # Q_intertia = 2*U*(A_t_pl - A_t) + U**2*(A_2 - A_1)/L*delta_t
    Q_intertia = 2*U #*(A_t_pl - A_t) + U**2*(A_2 - A_1)/L*delta_t
    Q_press = -g*A_bar*(H2 - H1)/L*delta_t
    Q_friction = g *(n/c)**2*abs(U)*delta_t/R_bar**(4./3.)

    return (Q_last + Q_intertia + Q_press)/(1+Q_friction)

Q_0 = 0
H1 = 2.01
H2 = 1.
Z1 = 2.
Z2 = 1.
b = 2.
L = 400.
n = 0.01
q = Q(Q_0, H1, H2, Z1, Z2, b, L, n)

