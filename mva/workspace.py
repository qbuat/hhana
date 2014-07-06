import os

from rootpy.plotting import Hist, Hist2D
from rootpy.io import root_open
from rootpy.stats import histfactory
from rootpy.utils.path import mkdir_p

from . import log; log = log[__name__]
from . import CONST_PARAMS, CACHE_DIR, MMC_MASS, POI
from .categories import CATEGORIES

import pickle
import os


def write_workspaces(path, prefix, year_mass_category_channel,
                     controls=None,
                     silence=False):
    log.info("writing workspaces ...")
    if controls is None:
        controls = []
    if not os.path.exists(path):
        mkdir_p(path)
    for year, mass_category_channel in year_mass_category_channel.items():
        # write workspaces for each year
        for mass, category_channel in mass_category_channel.items():
            if isinstance(controls, dict):
                if isinstance(controls[year], dict):
                    mass_controls = controls[year][mass].values()
                else:
                    mass_controls = controls[year]
            else:
                mass_controls = controls
            channels = []
            # make workspace for each category
            # include the control region in each
            for category, channel in category_channel.items():
                name = "{0}_{1}_{2}_{3}".format(
                    prefix, year % 1000, category, mass)
                log.info("writing {0} ...".format(name))
                # make workspace
                measurement = histfactory.make_measurement(
                    name, [channel] + mass_controls,
                    POI=POI,
                    const_params=CONST_PARAMS)
                workspace = histfactory.make_workspace(measurement, name=name,
                                                       silence=silence)
                with root_open(os.path.join(path, '{0}.root'.format(name)),
                               'recreate') as workspace_file:
                    workspace.Write()
                    # mu=1 for Asimov data
                    #measurement.SetParamValue('SigXsecOverSM', 1)
                    histfactory.write_measurement(measurement,
                        root_file=workspace_file,
                        xml_path=os.path.join(path, name),
                        silence=silence)
                channels.append(channel)
            # make combined workspace
            name = "{0}_{1}_combination_{2}".format(prefix, year % 1000, mass)
            log.info("writing {0} ...".format(name))
            measurement = histfactory.make_measurement(
                name, channels + mass_controls,
                POI=POI,
                const_params=CONST_PARAMS)
            workspace = histfactory.make_workspace(measurement, name=name,
                                                   silence=silence)
            with root_open(os.path.join(path, '{0}.root'.format(name)),
                           'recreate') as workspace_file:
                workspace.Write()
                # mu=1 for Asimov data
                #measurement.SetParamValue('SigXsecOverSM', 1)
                histfactory.write_measurement(measurement,
                    root_file=workspace_file,
                    xml_path=os.path.join(path, name),
                    silence=silence)
    # write combined workspaces over all years
    years = year_mass_category_channel.keys()
    if len(years) == 1:
        return
    masses = year_mass_category_channel[years[0]].keys()
    categories = year_mass_category_channel[years[0]][masses[0]].keys()
    for mass in masses:
        if isinstance(controls, dict):
            if isinstance(controls[year], dict):
                mass_controls = [control for year in years
                                 for control in controls[year][mass].values()]
            else:
                mass_controls = [control for year in years
                                 for control in controls[year]]
        else:
            mass_controls = controls
        channels = []
        # make workspace for each category
        # include the control region in each
        # TODO: categories might be different across years
        """
        for category in categories:
            cat_channels = [year_mass_category_channel[year][mass][category]
                            for year in years]
            name = "{0}_full_{1}_{2}".format(
                prefix, category, mass)
            log.info("writing {0} ...".format(name))
            # make workspace
            measurement = histfactory.make_measurement(
                name, cat_channels + mass_controls,
                POI=POI,
                const_params=CONST_PARAMS)
            workspace = histfactory.make_workspace(measurement, name=name,
                                                   silence=silence)
            with root_open(os.path.join(path, '{0}.root'.format(name)),
                           'recreate') as workspace_file:
                workspace.Write()
                # mu=1 for Asimov data
                #measurement.SetParamValue('SigXsecOverSM', 1)
                histfactory.write_measurement(measurement,
                    root_file=workspace_file,
                    xml_path=os.path.join(path, name),
                    silence=silence)
            channels.extend(cat_channels)
        """
        channels = [chan for year in years
                    for chan in year_mass_category_channel[year][mass].values()]
        # make combined workspace
        name = "{0}_full_combination_{1}".format(prefix, mass)
        log.info("writing {0} ...".format(name))
        measurement = histfactory.make_measurement(
            name, channels + mass_controls,
            POI=POI,
            const_params=CONST_PARAMS)
        workspace = histfactory.make_workspace(measurement, name=name,
                                               silence=silence)
        with root_open(os.path.join(path, '{0}.root'.format(name)),
                       'recreate') as workspace_file:
            workspace.Write()
            # mu=1 for Asimov data
            #measurement.SetParamValue('SigXsecOverSM', 1)
            histfactory.write_measurement(measurement,
                root_file=workspace_file,
                xml_path=os.path.join(path, name),
                silence=silence)


def mva_workspace(analysis, categories, masses,
                  clf_mass=None,
                  clf_bins='optimal',
                  unblind=False,
                  systematics=False,
                  cuts=None):
    hist_template = Hist(5, 0, 1.5, type='D')
    controls = analysis.make_var_channels(
        hist_template, 'dEta_tau1_tau2',
        CATEGORIES['mva_workspace_controls'],
        analysis.target_region,
        include_signal=True, masses=masses,
        systematics=systematics)
    mass_category_channel = {}
    for category in analysis.iter_categories(categories):
        for mass in masses:
            clf = analysis.get_clf(category, load=True,
                                   mass=clf_mass or mass,
                                   transform=True)
            if clf_bins == 'optimal':
                # get the binning (see the optimize-binning script)
                clf_bins = clf.binning(analysis.year, overflow=1E5)
                log.info("binning: {0}".format(str(clf_bins)))
            elif isinstance(clf_bins, basestring):
                clf_bins = int(clf_bins)
            # construct a "channel" for each mass point
            scores, channel = analysis.clf_channels(
                clf, category,
                region=analysis.target_region,
                bins=clf_bins,
                mass=mass,
                mode='workspace',
                systematics=systematics,
                cuts=cuts,
                unblind=unblind or 2,
                hybrid_data=not unblind,
                uniform=True)
            if mass not in mass_category_channel:
                mass_category_channel[mass] = {}
            mass_category_channel[mass][category.name] = channel
    return mass_category_channel, controls


def cuts_workspace(analysis, categories, masses,
                   unblind=False,
                   systematics=False,
                   cuts=None):
    channels = {}
    for category in analysis.iter_categories(categories):
        if isinstance(category.limitbins, dict):
            binning = category.limitbins[analysis.year]
        else:
            binning = category.limitbins
        hist_template = Hist(binning, type='D')
        for mass in masses:
            channel = analysis.get_channel_array(
                {MMC_MASS: hist_template},
                category=category,
                region=analysis.target_region,
                cuts=cuts,
                include_signal=True,
                mass=mass,
                mode='workspace',
                systematics=systematics,
                hybrid_data=None if unblind else {MMC_MASS:(100., 140.)},
                uniform=True)[MMC_MASS]
            if mass not in channels:
                channels[mass] = {}
            channels[mass][category.name] = channel
    return channels, []


def mass_workspace(analysis, categories, masses,
                   systematics=False):
    hist_template = Hist(30, 50, 200, type='D')
    channels = {}
    for category in analysis.iter_categories(categories):
        clf = analysis.get_clf(category, load=True, mass=125)
        scores = analysis.get_scores(
            clf, category, target_region,
            masses=[125], mode='combined',
            systematics=False,
            unblind=True)
        bkg_scores = scores.bkg_scores
        sig_scores = scores.all_sig_scores[125]
        min_score = scores.min_score
        max_score = scores.max_score
        bkg_score_hist = Hist(category.limitbins, min_score, max_score, type='D')
        sig_score_hist = bkg_score_hist.Clone()
        hist_scores(bkg_score_hist, bkg_scores)
        _bkg = bkg_score_hist.Clone()
        hist_scores(sig_score_hist, sig_scores)
        _sig = sig_score_hist.Clone()
        sob_hist = (1 + _sig / _bkg)
        _log = math.log
        for bin in sob_hist.bins(overflow=True):
            bin.value = _log(bin.value)
        log.info(str(list(sob_hist.y())))
        for mass in masses:
            channel = analysis.get_channel_array(
                {MMC_MASS: VARIABLES[MMC_MASS]},
                templates={MMC_MASS: hist_template},
                category=category,
                region=analysis.target_region,
                include_signal=True,
                weight_hist=sob_hist,
                clf=clf,
                mass=mass,
                scale_125=False, # CHANGE
                mode='workspace',
                systematics=systematics)[MMC_MASS]
            if mass not in channels:
                channels[mass] = {}
            channels[mass][category.name] = channel
    return channels, []


def mass2d_workspace(analysis, categories, masses,
                     systematics=False):
    hist_template = Hist2D(250, 0, 250, 200, -1, 1, type='D')
    channels = {}
    for category in analysis.iter_categories(categories):
        clf = analysis.get_clf(category, load=True)
        for mass in masses:
            channel = analysis.get_channel_array(
                {MMC_MASS: hist_template},
                category=category,
                region=analysis.target_region,
                clf=clf,
                include_signal=True,
                mass=mass,
                mode='workspace',
                systematics=systematics,
                ravel=False)[MMC_MASS]
            if mass not in channels:
                channels[mass] = {}
            channels[mass][category.name] = channel
    return channels, []
