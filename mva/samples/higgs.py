# stdlib imports
import os
import pickle
# rootpy imports
from rootpy.io import root_open
from rootpy.stats import histfactory

# Higgs cross sections and branching ratios
import yellowhiggs

# local imports
from . import log
from .. import ETC_DIR, CACHE_DIR, DAT_DIR
from .sample import MC, Signal

TAUTAUHADHADBR = 0.4197744 # = (1. - 0.3521) ** 2

class Higgs(MC, Signal):
    MASSES = range(100, 155, 5)
    MODES = ['Z', 'W', 'gg', 'VBF']
    MODES_COMBINED = [['Z', 'W'], ['gg'], ['VBF']]
    MODES_DICT = {
        'gg': ('ggf', 'PowPyth_', 'PowPyth8_AU2CT10_'),
        'VBF': ('vbf', 'PowPyth_', 'PowPyth8_AU2CT10_'),
        'Z': ('zh', 'Pyth8_AU2CTEQ6L1_', 'Pyth8_AU2CTEQ6L1_'),
        'W': ('wh', 'Pyth8_AU2CTEQ6L1_', 'Pyth8_AU2CTEQ6L1_'),
    }
    MODES_WORKSPACE = {
        'gg': 'ggH',
        'VBF': 'VBF',
        'Z': 'ZH',
        'W': 'WH',
    }

    # https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/HSG4Uncertainties
    # TODO: UPDATE
    QCD_SCALE = map(lambda token: token.strip().split(), '''\
    QCDscale_qqH     VBF    rest                   1.020/0.980
    QCDscale_qqH     VBF    boosted                1.014/0.986
    QCDscale_qqH     VBF    vbf                    1.020/0.980
    QCDscale_qqH     VBF    cuts_boosted_tight     1.014/0.986
    QCDscale_qqH     VBF    cuts_boosted_loose     1.014/0.986
    QCDscale_qqH     VBF    cuts_vbf_highdr_tight  1.020/0.980
    QCDscale_qqH     VBF    cuts_vbf_highdr_loose  1.020/0.980
    QCDscale_qqH     VBF    cuts_vbf_lowdr         1.020/0.980
    QCDscale_VH      VH     rest                   1.01/0.99
    QCDscale_VH      VH     boosted                1.041/0.960
    QCDscale_VH      VH     vbf                    1.01/0.99
    QCDscale_VH      VH     cuts_boosted_tight     1.041/0.960
    QCDscale_VH      VH     cuts_boosted_loose     1.041/0.960
    QCDscale_VH      VH     cuts_vbf_highdr_tight  1.01/0.99
    QCDscale_VH      VH     cuts_vbf_highdr_loose  1.01/0.99
    QCDscale_VH      VH     cuts_vbf_lowdr         1.01/0.99
    QCDscale_ggH     ggH    rest                   1.23/0.81
    QCDscale_ggH1in  ggH    rest                   0.92/1.09
    QCDscale_ggH1in  ggH    boosted                1.32/0.76
    QCDscale_ggH1in  ggH    cuts_boosted_tight     1.28/0.78
    QCDscale_ggH1in  ggH    cuts_boosted_loose     1.28/0.78
    QCDscale_ggH2in  ggH    boosted                0.93/1.08
    QCDscale_ggH2in  ggH    vbf                    1.26/0.80
    QCDscale_ggH2in  ggH    cuts_boosted_tight     0.96/1.05
    QCDscale_ggH2in  ggH    cuts_boosted_loose     0.97/1.03
    QCDscale_ggH2in  ggH    cuts_vbf_highdr_tight  1.26/0.79
    QCDscale_ggH2in  ggH    cuts_vbf_highdr_loose  1.26/0.79
    QCDscale_ggH2in  ggH    cuts_vbf_lowdr         1.25/0.80'''.split('\n'))

    UE_UNCERT = map(lambda token: token.strip().split(), '''\
    ATLAS_UE_qq  VBF      vbf                      1.080/0.920
    ATLAS_UE_qq  VBF      boosted                  1.050/0.950
    ATLAS_UE_qq  VBF      cuts_vbf_lowdr           1.110/0.890
    ATLAS_UE_qq  VBF      cuts_vbf_highdr_tight    1.080/0.920
    ATLAS_UE_qq  VBF      cuts_vbf_highdr_loose    1.030/0.970
    ATLAS_UE_qq  VBF      cuts_boosted_tight       1.090/0.910
    ATLAS_UE_qq  VBF      cuts_boosted_loose       1.020/0.980
    ATLAS_UE_gg  ggH      vbf                      1.010/0.990
    ATLAS_UE_gg  ggH      boosted                  1.010/0.990
    ATLAS_UE_gg  ggH      cuts_vbf_lowdr           1.006/0.994
    ATLAS_UE_gg  ggH      cuts_vbf_highdr_tight    1.450/0.550
    ATLAS_UE_gg  ggH      cuts_vbf_highdr_loose    1.170/0.830
    ATLAS_UE_gg  ggH      cuts_boosted_tight       1.010/0.990
    ATLAS_UE_gg  ggH      cuts_boosted_loose       1.160/0.840'''.split('\n'))

    PDF_ACCEPT_NORM_UNCERT = map(lambda token: token.strip().split(), '''\
    pdf_Higgs_qq_ACCEPT  VBF      vbf                      1.012/0.988
    pdf_Higgs_qq_ACCEPT  VBF      boosted                  1.010/0.990
    pdf_Higgs_qq_ACCEPT  VBF      cuts_vbf_lowdr           1.014/0.986
    pdf_Higgs_qq_ACCEPT  VBF      cuts_vbf_highdr_tight    1.010/0.990
    pdf_Higgs_qq_ACCEPT  VBF      cuts_vbf_highdr_loose    1.015/0.985
    pdf_Higgs_qq_ACCEPT  VBF      cuts_boosted_tight       1.033/0.967
    pdf_Higgs_qq_ACCEPT  VBF      cuts_boosted_loose       1.010/0.990
    pdf_Higgs_gg_ACCEPT  ggH      vbf                      1.054/0.946
    pdf_Higgs_gg_ACCEPT  ggH      boosted                  1.059/0.941
    pdf_Higgs_gg_ACCEPT  ggH      cuts_vbf_lowdr           1.047/0.953
    pdf_Higgs_gg_ACCEPT  ggH      cuts_vbf_highdr_tight    1.052/0.948
    pdf_Higgs_gg_ACCEPT  ggH      cuts_vbf_highdr_loose    1.054/0.946
    pdf_Higgs_gg_ACCEPT  ggH      cuts_boosted_tight       1.062/0.938
    pdf_Higgs_gg_ACCEPT  ggH      cuts_boosted_loose       1.056/0.944'''.split('\n'))

    PDF_ACCEPT_SHAPE_UNCERT = map(lambda token: token.strip().split(), '''\
    pdf_Higgs_qq_ACCEPT  VBF  vbf      h_VBF_vbf_{0}TeV_Up/h_VBF_vbf_{0}TeV_Down
    pdf_Higgs_qq_ACCEPT  VBF  boosted  h_VBF_boosted_{0}TeV_Up/h_VBF_boosted_{0}TeV_Down
    pdf_Higgs_qq_ACCEPT  ggH  vbf      h_gg_vbf_{0}TeV_Up/h_gg_vbf_{0}TeV_Down
    pdf_Higgs_qq_ACCEPT  ggH  boosted  h_gg_boosted_{0}TeV_Up/h_gg_boosted_{0}TeV_Down'''.split('\n'))


    #GEN_QMASS = map(lambda token: token.strip().split(), '''\
    #Gen_Qmass_ggH    ggH    VBF              1.19/0.81
    #Gen_Qmass_ggH    ggH    boosted          1.24/0.76
    #Gen_Qmass_ggH    ggH    rest             1.04/0.96'''.split('\n'))

    PDF_ACCEPT_file = root_open(
        os.path.join(DAT_DIR, 'ShapeUnc_PDF_hh.root'), 'read')
    #QCDscale_ggH3in_file = root_open(
    #    os.path.join(ETC_DIR, 'QCDscale_ggH3in.root'), 'read')
    NORM_BY_THEORY = True

    def __init__(self, year,
                 mode=None, modes=None,
                 mass=None, masses=None,
                 sample_pattern=None, # i.e. PowhegJimmy_AUET2CT10_ggH{0:d}_tautauInclusive
                 ggf_weight=True,
                 suffix=None,
                 label=None,
                 inclusive_decays=False,
                 **kwargs):
        self.inclusive_decays = inclusive_decays
        if masses is None:
            if mass is not None:
                assert mass in Higgs.MASSES
                masses = [mass]
            else:
                # default to 125
                masses = [125]
        else:
            assert len(masses) > 0
            for mass in masses:
                assert mass in Higgs.MASSES
            assert len(set(masses)) == len(masses)

        if modes is None:
            if mode is not None:
                assert mode in Higgs.MODES
                modes = [mode]
            else:
                # default to all modes
                modes = Higgs.MODES
        else:
            assert len(modes) > 0
            for mode in modes:
                assert mode in Higgs.MODES
            assert len(set(modes)) == len(modes)

        name = 'Signal'

        str_mode = ''
        if len(modes) == 1:
            str_mode = modes[0]
            name += '_%s' % str_mode
        elif len(modes) == 2 and set(modes) == set(['W', 'Z']):
            str_mode = 'V'
            name += '_%s' % str_mode

        str_mass = ''
        if len(masses) == 1:
            str_mass = '%d' % masses[0]
            name += '_%s' % str_mass

        if label is None:
            label = '%s#font[52]{H}(%s)#rightarrow#tau#tau' % (
                str_mode, str_mass)

        if year == 2011:
            if suffix is None:
                suffix = '.mc11c'
            generator_index = 1
        elif year == 2012:
            if suffix is None:
                suffix = '.mc12a'
            generator_index = 2
        else:
            raise ValueError('No Higgs defined for year %d' % year)

        self.samples = []
        self.masses = []
        self.modes = []

        if sample_pattern is not None:
            assert len(modes) == 1
            for mass in masses:
                self.masses.append(mass)
                self.modes.append(modes[0])
                self.samples.append(sample_pattern.format(mass) + '.' + suffix)
        else:
            for mode in modes:
                generator = Higgs.MODES_DICT[mode][generator_index]
                for mass in masses:
                    self.samples.append('%s%sH%d_tautauhh%s' % (
                        generator, mode, mass, suffix))
                    self.masses.append(mass)
                    self.modes.append(mode)

        if len(self.modes) == 1:
            self.mode = self.modes[0]
        else:
            self.mode = None
        if len(self.masses) == 1:
            self.mass = self.masses[0]
        else:
            self.mass = None

        self.ggf_weight = ggf_weight
        self.ggf_weight_field = 'ggf_weight'
        super(Higgs, self).__init__(
            year=year, label=label, name=name, **kwargs)

    #def weight_systematics(self):
    #    systematics = super(Higgs, self).weight_systematics()
    #    if self.ggf_weight:
    #        systematics.update({
    #            'QCDscale_ggH1in'})
    #    return systematics

    def weight_fields(self):
        fields = super(Higgs, self).weight_fields()
        if self.ggf_weight:
            return fields + [
                self.ggf_weight_field,
            ]
        return fields

    def histfactory(self, sample, category, systematics=False):
        if not systematics:
            return
        if len(self.modes) != 1:
            raise TypeError(
                'histfactory sample only valid for single production mode')
        if len(self.masses) != 1:
            raise TypeError(
                'histfactory sample only valid for single mass point')

        # isolation systematic
        sample.AddOverallSys(
            'ATLAS_ANA_HH_{0:d}_Isolation'.format(self.year),
            1. - 0.06,
            1. + 0.06)

        mode = self.modes[0]

        if mode in ('Z', 'W'):
            _uncert_mode = 'VH'
        else:
            _uncert_mode = self.MODES_WORKSPACE[mode]

        # QCD_SCALE
        for qcd_scale_term, qcd_scale_mode, qcd_scale_category, values in self.QCD_SCALE:
            if qcd_scale_mode == _uncert_mode and qcd_scale_category == category.name:
                high, low = map(float, values.split('/'))
                sample.AddOverallSys(qcd_scale_term, low, high)

        # UE UNCERTAINTY
        for ue_term, ue_mode, ue_category, values in self.UE_UNCERT:
            if ue_mode == _uncert_mode and ue_category == category.name:
                high, low = map(float, values.split('/'))
                sample.AddOverallSys(ue_term, low, high)

        # PDF ACCEPTANCE UNCERTAINTY (OverallSys)
        for pdf_term, pdf_mode, pdf_category, values in self.PDF_ACCEPT_NORM_UNCERT:
            if pdf_mode == _uncert_mode and pdf_category == category.name:
                high, low = map(float, values.split('/'))
                sample.AddOverallSys(pdf_term, low, high)

        if self.year == 2011:
            energy = 7
        elif self.year == 2012:
            energy = 8
        else:
            raise ValueError(
                "collision energy is unknown for year {0:d}".format(self.year))

        # PDF ACCEPTANCE UNCERTAINTY (HistoSys)
        for pdf_term, pdf_mode, pdf_category, hist_names in self.PDF_ACCEPT_SHAPE_UNCERT:
            if pdf_mode == _uncert_mode and pdf_category == category.name:
                high_name, low_name = hist_names.format(energy).split('/')
                high, low = PDF_ACCEPT_file[high_name], PDF_ACCEPT_file[low_name]
                high = high*sample.hist
                low = low*sample.hist
                histsys = histfactory.HistoSys(
                    pdf_term, low=low, high=high)
                sample.AddHistoSys(histsys)

        # GEN_QMASS
        #for qmass_term, qmass_mode, qmass_category, values in self.GEN_QMASS:
        #    if qmass_mode == _qcd_scale_mode and qmass_category.lower() in category.name.lower():
        #        high, low = map(float, values.split('/'))
        #        sample.AddOverallSys(qmass_term, low, high)

        # BR_tautau
        _, (br_up, br_down) = yellowhiggs.br(
            self.mass, 'tautau', error_type='factor')
        sample.AddOverallSys('ATLAS_BR_tautau', br_down, br_up)

        # <NormFactor Name="mu_BR_tautau" Val="1" Low="0" High="200" />
        sample.AddNormFactor('mu_BR_tautau', 1., 0., 200., True)

        #mu_XS[energy]_[mode]
        #_, (xs_up, xs_down) = yellowhiggs.xs(
        #    energy, self.mass, self.MODES_DICT[self.mode][0],
        #    error_type='factor')
        #sample.AddOverallSys(
        #    'mu_XS{0:d}_{1}'.format(energy, self.MODES_WORKSPACE[self.mode]),
        #    xs_down, xs_up)
        sample.AddNormFactor(
            'mu_XS{0:d}_{1}'.format(energy, self.MODES_WORKSPACE[self.mode]),
            1., 0., 200., True)

        # https://twiki.cern.ch/twiki/bin/viewauth/AtlasProtected/HSG4Uncertainties
        # pdf uncertainty
        if mode == 'gg':
            if energy == 8:
                sample.AddOverallSys('pdf_Higgs_gg', 0.93, 1.08)
            else: # 7 TeV
                sample.AddOverallSys('pdf_Higgs_gg', 0.92, 1.08)
        else:
            if energy == 8:
                sample.AddOverallSys('pdf_Higgs_qq', 0.97, 1.03)
            else: # 7 TeV
                sample.AddOverallSys('pdf_Higgs_qq', 0.98, 1.03)

        #EWK NLO CORRECTION FOR VBF ONLY
        if mode == 'VBF':
            sample.AddOverallSys('NLO_EW_Higgs', 0.98, 1.02)

        # QCDscale_ggH3in MVA only UPDATE THIS!!!
        #if mode == 'gg' and category.name == 'vbf':
        #    up = self.QCDscale_ggH3in_file.up_fit
        #    dn = self.QCDscale_ggH3in_file.dn_fit
        #    nom = sample.hist
        #    up_hist = nom.clone(shallow=True, name=nom.name + '_QCDscale_ggH3in_UP')
        #    dn_hist = nom.clone(shallow=True, name=nom.name + '_QCDscale_ggH3in_DOWN')
        #    up_hist *= up
        #    dn_hist *= dn
        #    shape = histfactory.HistoSys('QCDscale_ggH3in',
        #        low=dn_hist,
        #        high=up_hist)
        #    norm, shape = histfactory.split_norm_shape(shape, nom)
        #    sample.AddHistoSys(shape)

    def xsec_kfact_effic(self, isample):
        # use yellowhiggs for cross sections
        xs, _ = yellowhiggs.xsbr(
            self.energy, self.masses[isample],
            Higgs.MODES_DICT[self.modes[isample]][0], 'tautau')
        log.debug("{0} {1} {2} {3} {4} {5}".format(
            self.samples[isample],
            self.masses[isample],
            self.modes[isample],
            Higgs.MODES_DICT[self.modes[isample]][0],
            self.energy,
            xs))
        if not self.inclusive_decays:
            xs *= TAUTAUHADHADBR
        kfact = 1.
        effic = 1.
        return xs, kfact, effic


class InclusiveHiggs(MC, Signal):
    # for overlap study
    SAMPLES = {
        'ggf': 'PowPyth8_AU2CT10_ggH125p5_inclusive.mc12b',
        'vbf': 'PowPyth8_AU2CT10_VBFH125p5_inclusive.mc12b',
        'zh': 'Pyth8_AU2CTEQ6L1_ZH125p5_inclusive.mc12b',
        'wh': 'Pyth8_AU2CTEQ6L1_WH125p5_inclusive.mc12b',
        'tth': 'Pyth8_AU2CTEQ6L1_ttH125p5_inclusive.mc12b',
    }

    def __init__(self, mode=None, **kwargs):
        self.energy = 8
        if mode is not None:
            self.modes = [mode]
            self.masses = [125]
            self.samples = [self.SAMPLES[mode]]
        else:
            self.masses = [125] * 5
            self.modes = ['ggf', 'vbf', 'zh', 'wh', 'tth']
            self.samples = [
                'PowPyth8_AU2CT10_ggH125p5_inclusive.mc12b',
                'PowPyth8_AU2CT10_VBFH125p5_inclusive.mc12b',
                'Pyth8_AU2CTEQ6L1_ZH125p5_inclusive.mc12b',
                'Pyth8_AU2CTEQ6L1_WH125p5_inclusive.mc12b',
                'Pyth8_AU2CTEQ6L1_ttH125p5_inclusive.mc12b',
            ]
        super(InclusiveHiggs, self).__init__(
            year=2012, name='Signal', label='Signal',
            ntuple_path='ntuples/prod_v29',
            student='hhskim_overlap',
            **kwargs)

    def xsec_kfact_effic(self, isample):
        # use yellowhiggs for cross sections
        xs, _ = yellowhiggs.xs(
            self.energy, self.masses[isample], self.modes[isample])
        log.debug("{0} {1} {2} {3} {4}".format(
            self.samples[isample],
            self.masses[isample],
            self.modes[isample],
            self.energy,
            xs))
        kfact = 1.
        effic = 1.
        return xs, kfact, effic
