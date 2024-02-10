import control as ctrl
import matplotlib.pyplot as plt 
import numpy as np
s = ctrl.tf([1,0],[0,1])


def PT2(f,d):
    w = f*2*np.pi 
    return ctrl.tf([w**2],[1,2*d*w,w**2])


def notch(fn,dn,fd,dd):
    return 1/PT2(fn,dn) * PT2(fd,dd)

def step(G,**kargs):
    t,y = ctrl.step_response(G)
    plt.plot(t,y,**kargs)

def pade(t,N):
    B,A = ctrl.pade(t,N)
    return ctrl.tf(B,A)

