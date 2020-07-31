---
title: "Developing Sequence Stratigraphic Modeling in Landlab"
tags:
  - Python
  - geosciences
  - modeling
authors:
  - name: Michael S. Steckler
    orcid: 
    affiliation: 1
  - name: Eric W.H. Hutton
    orcid: 0000-0002-5864-6459
    affiliation: 2
  - name: David Ologan
    orcid: 
    affiliation: 
  - name: Gregory E. Tucker
    orcid: 0000-0003-0364-5800
    affiliation: 2, 3, 4
affiliations:
  - name: 
    index: 1
  - name: Community Surface Dynamics Modeling System, University of Colorado Boulder, USA
    index: 2
  - name: Cooperative Institute for Research in Environmental Sciences (CIRES), University of Colorado Boulder, USA
    index: 3
  - name: Department of Geological Sciences, University of Colorado Boulder, USA
    index: 4
date: 30 July 2020
bibliography: paper.bib

---

Summary
=======


The accumulation of layers of sediment, or stratigraphy, at continental
margins is the result of the interplay of the creation of accommodation
space and its filling by sediments. Accommodation space is shaped by
relative sea level, a combination of eustatic sea level and multiple
mechanisms that cause subsidence (or uplift) to create (or destroy)
accommodation space, by changes in the morphology of the seafloor.
Sediments fill the space as a function of supply rate, transport processes,
and deposition and erosional processes.  These processes are coupled,
sediment deposition is controlled by seafloor morphology and the buildup
of sedimentary deposits in turn modifies the seafloor morphology and local
subsidence through sediment compaction and isostasy (e.g., @reynolds1991role). 

Sequence is a modular 2D (i.e., profile) sequence stratigraphic model
that is written in Python and implemented within the Landlab framework
(@hobley2017creative, @barnhart2020landlab). The model geophysical
framework includes major factors that affect accommodation space: tectonics
and faulting, eustatic sea level, flexural isostatic compensation of
sediment and water, and sediment compaction. Most sediment transport and
deposition occurs during infrequent energetic events (i.e., storms, floods).
For longer-time frame accumulation of sedimentary strata, Sequence uses
a scale-integral approach in which differential equations represent the
net effect of sediment transport and deposition for each depositional
environment over a longer (i.e., ~100 y) timescale. The basic framework
is a moving-boundary formulation with the coastal plain, continental
shelf, upper slope and lower slope/rise (@steckler1993modelling;
@syvitski2007predictiop). Submarine sediment transport and deposition
is modeled as nonlinear diffusion. Sediment lithology is tracked as a
mixture of two grain sizes corresponding to sand and mud with separate
transport functions. The components of the code are modular to
accommodate upgrades and inclusion of alternative formulations.
Sequence is appropriate for modeling stratigraphy on the 1,000s to
1,000,000s of year time scale.

Studies of the stratigraphy of continental margins and sedimentary
basin (e.g., @vail1977seismic, @posamentier1988eustatic) have
demonstrated that the interplay of sea level, subsidence and
sedimentation results in the formation of unconformity-bound packages
of sediments termed sequences.  The formation of sequences with the
development of characteristic unconformities such as a subaerial
sequence boundary, a transgressive ravinement surface, and a
submarine regressive erosion surface appears to be a robust feature
of all models that include distinct shoreline and clinoform breaks,
such as Sequence, whichever independent of the method that is used
for sediment transport.

Sequence generates 2-D stratigraphic cross section using yaml files
to set parameters for the runs and two column ascii files to set
variations of properties across the model or sea level through
time. Output is stored in NetCDF format. Ancillary plotting routines
enable plotting of cross sections and Wheeler diagrams (deposition vs.
time). 

Figure – cross section?

References
==========

