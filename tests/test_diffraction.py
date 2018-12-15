from __future__ import print_function

import numpy as np

from xrsdkit import scattering as xrs
from xrsdkit.tools import peak_math
from xrsdkit.system import System, Population

fcc_Al = Population(
    structure='crystalline',
    form='atomic',
    settings={'lattice':'cubic','centering':'F','space_group':'Fm-3m',
        'q_max':5.,'structure_factor_mode':'local','symbol':'Al'},
    parameters=dict(
        a={'value':4.046},
        hwhm_g={'value':0.002},
        hwhm_l={'value':0.0018}
        )
    )
hcp_spheres = Population(
    structure='crystalline',
    form='spherical',
    settings={'lattice':'hexagonal','centering':'HCP',
        'space_group':'P6(3)/mmc','q_max':0.6,
        'structure_factor_mode':'radial'},
    parameters=dict(
        a={'value':120.},
        c={'value':np.sqrt(8./3.)*120.,'constraint_expr':'hcp_spheres__a*sqrt(8./3.)'},
        hwhm_g={'value':0.002},
        hwhm_l={'value':0.002},
        r={'value':40.}
        )
    )

fcc_Al_system = System(
    fcc_Al=fcc_Al.to_dict(),
    sample_metadata={'source_wavelength':0.8265617}
    )
hcp_sphere_system = System(
    hcp_spheres=hcp_spheres.to_dict(),
    sample_metadata={'source_wavelength':0.8265617}
    )

glassy_Al = Population(
    structure='disordered',
    form='atomic',
    settings={'interaction':'hard_spheres','symbol':'Al'},
    parameters=dict(
        r_hard={'value':4.046*np.sqrt(2)/4},
        v_fraction={'value':0.6},
        I0={'value':1.E5}
        )
    )

glassy_Al_system = System(glassy_Al=glassy_Al.to_dict())

mixed_Al_system = System(
    glassy_Al=glassy_Al.to_dict(),
    fcc_Al=fcc_Al.to_dict(),
    sample_metadata={'source_wavelength':0.8265617}
    )

#def test_Al_scattering():
#    qvals = np.arange(1.,5.,0.001)
#    I_fcc = fcc_Al_system.compute_intensity(qvals,0.8265616)
#    I_gls = glassy_Al_system.compute_intensity(qvals,0.8265616)
#    I_mxd = mixed_Al_system.compute_intensity(qvals,0.8265616)

    #from matplotlib import pyplot as plt
    #plt.figure(4)
    #plt.plot(qvals,I_fcc)
    #plt.plot(qvals,I_gls)
    #plt.plot(qvals,I_mxd)
    #plt.legend(['fcc','glassy','mixed'])
    #plt.show()

def test_sphere_scattering():
    qvals = np.arange(0.02,0.6,0.001)
    I_sl = hcp_sphere_system.compute_intensity(qvals) 
    
def test_gaussian():
    qvals = np.arange(0.01,4.,0.01)
    for hwhm in [0.01,0.03,0.05,0.1]:
        g = peak_math.gaussian(qvals-2.,hwhm)
        #intg = np.sum(0.01*g)
        #print('approx. integral of gaussian with hwhm {}: {}'\
        #    .format(hwhm,intg))

def test_lorentzian():
    qvals = np.arange(0.01,4.,0.01)
    for hwhm in [0.01,0.03,0.05,0.1]:
        l = peak_math.lorentzian(qvals-2.,hwhm)
        #intl = np.sum(0.01*l)
        #print('approx. integral of lorentzian with hwhm {}: {}'\
        #    .format(hwhm,intl))

def test_voigt():
    qvals = np.arange(0.01,4.,0.01)
    for hwhm_g in [0.01,0.03,0.05,0.1]:
        for hwhm_l in [0.01,0.03,0.05,0.1]:
            v = peak_math.voigt(qvals-2.0,hwhm_g,hwhm_l)
            #intv = np.sum(0.01*v)
            #print('approx. integral of voigt '\
            #    'with gaussian hwhm {} and lorentzian hwhm {}: {}'\
            #    .format(hwhm_g,hwhm_l,intv))

