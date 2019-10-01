# Copyright 2019 Andrew Schaeffer
#
# This file is part of StDb.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#!/usr/bin/env python
# encoding: utf-8
''' 
        Program: gen_stdb.py

        Description:
        Create Station Database dictionary based on an input file in one of two
        formats:
        1) chS csv:          -------Start---------   --------END----------
         NET,STA,locID,CHAN,YYYY-MM-DD,HH:MM:SS.SSS,YYYY-MM-DD,HH:MM:SS.SSS,lat,lon
        
        2) IPO SPC                 --Start--- ---END----
         NET STA CHAN lat lon elev YYYY-MM-DD YYYY-MM-DD

        The station dictionary contains keys which are named NET.STA.CHAN, where CHAN
        is a two character representation of the desired channel (ex, BH, HH, LH).
        Within each KEY is the set of data used in later programs to define the 
        station information. The data is stored in a dictionary, with each dictionary 
        element being an object of Class stdb.StDbElement. An item has:
            stdb[stkey]:
                 .station
                 .network
                 .altnet
                 .channel
                 .location
                 .latitude
                 .longitude
                 .elevation
                 .startdate
                 .enddate
                 .polarity
                 .azcorr
                 .status
                 .stla (compatibility only)
                 .stlo (compatibility only)
                 .cha (compatibility only)
                 .dstart (compatibility only)
                 .dend (compatibility only)

'''


from sys import exit
import os.path as osp
from obspy.core import UTCDateTime
from stdb import write_db
from stdb import StDbElement
from optparse import OptionParser


class MyParser(OptionParser):
    def format_epliog(self, formatter):
            return self.epilog

if __name__=='__main__':

    # Get options
    parser = MyParser(usage="Usage: %prog [options] <station list>",
                 description="Script to generate a pickled station database file. Options include generating a " \
                 "version 2 or version 1 database file.",
                 epilog="""
Input File Type 1 (chS csv):                                                 
NET[:NET2:...],STA,LOC[:LOC2:...],CHN,YYYY-MM-DD,HH:MM:SS.SSS,YYYY-MM-DD,HH:MM:SS.SSS,lat,lon,elev,pol,azcor,status
                                                        
Input File Type 2 (IPO SPC):                                                 
NET STA CHAN lat lon elev YYYY-MM-DD YYYY-MM-DD          

                                                                                                                                        
Output File Types:                                                            
v2                                                                          
Each element corresponding to each dictionary key is saved as stdb.StbBElement class,
rather than as a list type (as is v1).                                         
                                                                                                                                                             
v1                                                                          
Each element corresponding to each dictionary key is saved as a list object. When the dictionary
is loaded, then the list was converted into a class meta_dict. Note that the stdb.io.load_db
function has been overloaded such that it can load both v2 and v1 type station dictionary
pickle files.                                                                   
                                                                                                                                                    

Andrew Schaeffer, 25 August 2015\n\n
    """)
    parser.add_option("-t", "-T", "--type", action="store", type="int", dest="dbver", default=2, \
        help="Specify the station database version type. v2 (specify 2) is default, and give the " \
        "more updated database with helper functions and more details. v1 (specify 1) gives the " \
        "older legacy format station database.")
    parser.add_option("-L", "--long-keys", action="store_true", dest="lkey", default=False, \
        help="Specify Key format. Default is Net.Stn. Long keys are Net.Stn.Chn")
    parser.add_option("-c", "--cPickle", action="store_true", dest="use_cPickle", default=False, \
        help="Specify pickle format type. Default uses pickle, specify to use cPickle")
    parser.add_option("-a", "--ascii", action="store_false", dest="use_binary", default=True, \
        help="Specify to write ascii Pickle files instead of binary. Ascii are larger file size, " \
        "but more likely to be system independent.")
    (opts, args) = parser.parse_args()
    
    if not osp.exists(args[0]):
        parser.error("Input File " + args[0] + " does not exist")
    if opts.dbver != 1 and opts.dbver != 2:
        parser.error("Please specify valid db version (1 or 2)")

    # Check Extension    
    ext = osp.splitext(args[0])[1]
    if ext != ".pkl":
        # Station List...Pickle it.
        print ("Parse Station List " + args[0])

        ofn = args[0]
        if ofn.find(".csv"):
            if (len(ofn)-4) == ofn.find(".csv"):
                ofn = osp.splitext(ofn)[0]
        pklfile = ofn + ".pkl"
        
        fin = open(args[0],'r')
        stations = {}
        for line in fin:
            line = line.strip()
            if len(line) == 0 or line[0] == "#":
                continue
            if len(line.split(',')) > 6:
                line = line.split(',')
                # Networks
                nets = line[0].split(':')
                if len(nets) == 1:
                    net = nets[0]
                    altnet = []
                else:
                    net = nets[0]
                    altnet = nets[1:]
                # Required Station Parameters
                stn = line[1]
                # Required Location Parameters
                loc = line[2].split(':')
                # Required Channel Parmaeters
                chn = line[3][0:2]
                # Required Timing Parameters
                stdt = line[4]; sttm = line[5]; eddt = line[6]; edtm = line[7]
                # Required Position Parameters
                lat = float(line[8]); lon = float(line[9])
                
                # Set Default values for Optional elements 
                elev = 0.; pol = 1.; azcor = 0.
                if len(line) >= 11:
                    elev = float(line[10])
                if len(line) >= 12:
                    pol = float(line[11])
                if len(line) >= 13:
                    azcor = float(line[12])
                if len(line) == 14:
                    status = line[13]
                    
            elif len(line.split()) > 6 or len(line.split('\t')) > 6:
                if len(line.split()) > 6:
                    line = line.split()
                else:
                    line = line.split('\t')
                net = line[0]; stn = line[1]; chn = line[2][0:2]
                stdt = line[6]; eddt = line[7]
                lat = float(line[3]); lon = float(line[4])
                elev = float(line[5])
                altnet = []; status = ""; azcor = 0.; pol = 0.; loc = ""

            # Now Add lines to station Dictionary
            if opts.lkey:
                key = "{0:s}.{1:s}.{2:2s}".format(net.strip(), stn.strip(), chn.strip())
            else:
                key = "{0:s}.{1:s}".format(net.strip(), stn.strip())
            if not stations.has_key(key):
                if opts.dbver == 2:
                    stations[key] = StDbElement(network=net, altnet=altnet, station=stn, \
                        channel=chn,location=loc, latitude=lat, longitude=lon, elevation=elev, \
                        polarity=pol, azcorr=azcor, startdate=UTCDateTime(stdt), \
                        enddate=UTCDateTime(eddt), restricted_status=status)
                else:
                    stations[key] = [net, stn, lat, lon, chn,UTCDateTime(stdt), UTCDateTime(eddt)]
                print ("Adding key: " + key)
            else:
                print ("Warning: Key " + key + " already exists...Skip")

        # Save and Pickle the station database
        print ("  Pickling type {0:d} to {1:s}".format(opts.dbver, pklfile))
        write_db(fname=pklfile, stdb=stations, binp=opts.use_binary)
    else:
        print ("Error: Must supply a station list, not a Pickle File")
        exit()