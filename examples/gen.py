import ROOT
from ROOT import TFile, TH1F, TH2F, TH3F, TTree, RooRealVar, RooGenericPdf, RooArgList
import numpy as np

file = TFile.Open('example.root','RECREATE')

#---------------#
# General setup #
#---------------#
def generate_hist(func, nevents=10000):
    if isinstance(func, TF1):
        hist = TH1F(
            'h'+func.GetName(), func.GetName(),
            25, func.GetXaxis().GetXmin(), func.GetXaxis().GetXmax()
        )
        for i in range(nevents):
            hist.Fill(func.GetRandom())

    elif isinstance(func, TF2):
        hist = TH2F(
            'h'+func.GetName(), func.GetName(),
            25, func.GetXaxis().GetXmin(), func.GetXaxis().GetXmax(),
            25, func.GetXaxis().GetXmin(), func.GetXaxis().GetXmax(),
        )
        x, y = -1, -1
        for i in range(nevents):
            func.GetRandom2(x, y)
            hist.Fill(x,y)
    else:
        hist = TH3F(
            'h'+func.GetName(), func.GetName(),
            25, func.GetXaxis().GetXmin(), func.GetXaxis().GetXmax(),
            25, func.GetYaxis().GetXmin(), func.GetYaxis().GetXmax(),
            25, func.GetZaxis().GetXmin(), func.GetZaxis().GetXmax()
        )
        x, y, z = -1, -1, -1
        for i in range(nevents):
            func.GetRandom3(x,y,z)
            hist.Fill(x,y,z)
    
    return hist

def get_suffix(syst_name, var_name):
    return var_name if var_name == 'nominal' else f'{syst_name}_{var_name}'

def set_and_write(func, param_sets, syst_names):
    for i,pset in enumerate(param_sets):
        func.SetParameter(i,pset[1])
    file.WriteObject(generate_hist(func), f'{func.GetName()}_nominal')

    for i, (pset, syst_name) in enumerate(zip(param_sets, syst_names)):
        func.SetParameter(i, pset[0])
        file.WriteObject(generate_hist(func), f'{func.GetName()}_{syst_name}_down')
        func.SetParameter(i, pset[2])
        file.WriteObject(generate_hist(func), f'{func.GetName()}_{syst_name}_up')
        func.SetParameter(i, pset[1])

xvar = RooRealVar('x','x',)

#-------------#
# 1D examples #
#-------------#
bkg_1D = TF1("bkg_1D","TMath::Landau(x,0,[0],0)",50,250) # p0 -> falling speed
sig_1D = TF1("sig_1D","TMath::BreitWigner(x, [0], [1])",50,250) # p0 -> peak, p1-> width

bkg_1D_params = [[20, 30, 40]]
sig_1D_params = [
    [60, 80, 100],
    [20, 30, 40]
]

set_and_write(bkg_1D, bkg_1D_params, ['LandauSigma'])
set_and_write(sig_1D, sig_1D_params, ['BreitWignerMu','BreitWignerGamma'])

#-------------#
# 2D examples #
#-------------#
bkgA_2D = TF2("bkgA_2D","TMath::Landau(x,0,[0],0) * TMath::Landau(y,0,[1],0)",50,250,1000,3000) # p0, p1 -> falling speed
bkgB_2D = TF2("bkgB_2D","TMath::BreitWigner(x,[0],[1]) * TMath::Landau(y,0,[2],0)",50,250,1000,3000) # p0 -> peak, p1 -> width, p2 -> falling speed
sig_2D = TF2("sig_2D","TMath::BreitWigner(x,[0],[1]) * TMath::BreitWigner(y,[2],[3])",50,250,1000,3000) # p0, p2 -> peak; p1, p3 -> width

bkgA_2D_params = [
    bkg_1D_params[0],
    [100, 150, 200]
]

bkgB_2D_params = [
    sig_1D_params[0],
    sig_1D_params[1],
    bkgA_2D_params[1]
]

sig_2D_params = [
    sig_1D_params[0],
    sig_1D_params[1],
    [150, 170, 190],
    [70, 90, 110]
]

set_and_write(bkgA_2D, bkgA_2D_params, ['LandauSigmaX', 'LandauSigmaY'])
set_and_write(bkgB_2D, bkgB_2D_params, ['BreitWignerMuX', 'BreitWignerGammaX', 'LandauSigmaY'])
set_and_write(sig_2D, sig_2D_params, ['BreitWignerMuX', 'BreitWignerGammaX', 'BreitWignerMuY', 'BreitWignerGammaY'])