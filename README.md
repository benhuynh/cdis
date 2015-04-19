# cdis
caprivifloodlabels.R - Scrapes Caprivi flood data from GDACS and presents it in a clean .csv file.

rbplot.R - Creates reflectance vs band number plots for each basin of a given scene.

reflectance.py - Converts a series of hyperion band images to a .csv of correced reflectance values.

subset.sh - Subsets a series of hyperion band images into smaller ones based on given geographic coordinates.

subsetrb.sh - Runs subset.sh for each basin for a given scene.

Ex: ./subset.sh EO1H0360372003310110KV_1T
