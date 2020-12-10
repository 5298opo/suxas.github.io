#!/usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import argparse

dtmf = {(695, 1209): "1", (695, 1331): "2", (695, 1475): "3", (766, 1209): "4", (766, 1331): "5", (766, 1475): "6", (846, 1209): "7", (846, 1331): "8", (846, 1475): "9", (934, 1209): "*", (934, 1331): "0", (934, 1475): "#"}


parser = argparse.ArgumentParser(description="Extract phone numbers from an audio recording of the dial tones.")
parser.add_argument("-v", "--verbose", help="show a complete timeline", action="store_true")
parser.add_argument("-l", "--left", help="left channel only (if the sound is stereo)", action="store_true")
parser.add_argument("-r", "--right", help="right channel only (if the sound is stereo)", action="store_true")
parser.add_argument("-d", "--debug", help="show graphs to debug", action="store_true")
parser.add_argument("-t", type=int, metavar="F", help="acceptable frequency error (in hertz, 20 by default)", default=20)
parser.add_argument("-i", type=float, metavar='T', help="process by T seconds intervals (0.04 by default)", default=0.08)

parser.add_argument('file', type=argparse.FileType('r'))

args = parser.parse_args()


file = args.file.name
try:
    fps, data = wavfile.read(file)
except FileNotFoundError:
    print ("No such file:", file)
    exit()
except ValueError:
    print ("Impossible to read:", file)
    print("Please give a wav file.")
    exit()


if args.left and not args.right:
    if len(data.shape) == 2 and data.shape[1] == 2:
        data = np.array([i[0] for i in data])
    elif len(data.shape) == 1:
        print ("Warning: The sound is mono so the -l option was ignored.")
    else:
        print ("Warning: The sound is not mono and not stereo ("+str(data.shape[1])+" canals)... so the -l option was ignored.")


elif args.right and not args.left:
    if len(data.shape) == 2 and data.shape[1] == 2:
        data = np.array([i[1] for i in data])
    elif len(data.shape) == 1:
        print ("Warning: the sound is mono so the -r option was ignored.")
    else:
        print ("Warning: The sound is not mono and not stereo ("+str(data.shape[1])+" canals)... so the -r option was ignored.")

else:
    if len(data.shape) == 2: 
        data = data.sum(axis=1) # stereo

precision = args.i

duration = len(data)/fps

step = int(len(data)//(duration//precision))

debug = args.debug
verbose = args.verbose
c = ""

if debug:
    print("Warning:\nThe debug mode is very uncomfortable: you need to close each window to continue.\nFeel free to kill the process doing CTRL+C and then close the window.\n")

if verbose:
    print ("0:00 ", end='', flush=True)

try:
    for i in range(0, len(data)-step, step):
        signal = data[i:i+step]

        if debug:
            plt.subplot(311)
            plt.subplots_adjust(hspace=0.5)
            plt.title("audio (entire signal)")
            plt.plot(data)
            plt.xticks([])
            plt.yticks([])
            plt.axvline(x=i, linewidth=1, color='red')
            plt.axvline(x=i+step, linewidth=1, color='red')
            plt.subplot(312)
            plt.title("analysed frame")
            plt.plot(signal)
            plt.xticks([])
            plt.yticks([])
        fourier = np.fft.fft(signal)
        frequencies = np.fft.fftfreq(signal.size, d=1/fps)

        # Low
        debut = np.where(frequencies > 0)[0][0]
        fin = np.where(frequencies > 1050)[0][0]
        
        freq = frequencies[debut:fin]
        amp = abs(fourier.real[debut:fin])

        lf = freq[np.where(amp == max(amp))[0][0]]

        delta = args.t
        best = 0

        for f in [695, 766, 846, 934]:
            if abs(lf-f) < delta:
                delta = abs(lf-f)
                best = f

        if debug:
            plt.subplot(313)
            plt.title("Fourier transform")
            plt.plot(freq, amp)
            plt.yticks([])
            plt.annotate(str(int(lf))+"Hz", xy=(lf, max(amp)))

        lf = best

        # High
        debut = np.where(frequencies > 1100)[0][0]
        fin = np.where(frequencies > 2000)[0][0]

        freq = frequencies[debut:fin]
        amp = abs(fourier.real[debut:fin])

        hf = freq[np.where(amp == max(amp))[0][0]]

        delta = args.t
        best = 0

        for f in [1209, 1331, 1475]:
            if abs(hf-f) < delta:
                delta = abs(hf-f)
                best = f

        if debug:
            plt.plot(freq, amp)
            plt.annotate(str(int(hf))+"Hz", xy=(hf, max(amp)))

        hf = best

        if debug:
            if lf == 0 or hf == 0:
                txt = "Unknown dial tone"
            else: txt = str(lf)+"Hz + "+str(hf)+"Hz -> "+dtmf[(lf,hf)]
            plt.xlabel(txt)


        t = int(i//step * precision)

        if verbose and t > int((i-1)//step * precision):
            m = str(int(t//60))
            s = str(t%60)
            s = "0"*(2-len(s)) + s
            print ("\n"+m+":"+s+" ", end='', flush=True)

        if lf == 0 or hf == 0:
            if verbose:
                print(".", end='', flush=True)
            c = ""
        elif dtmf[(lf,hf)] != c or verbose:
            c = dtmf[(lf,hf)]
            print(c, end='', flush=True)

        if debug:
            plt.show()

    print()

except KeyboardInterrupt:
    print("\nCTRL+C detected: exiting...")
