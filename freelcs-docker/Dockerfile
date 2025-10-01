FROM ubuntu:24.04
USER root:root
COPY source_files/LoudnessCorrection.py source_files/loudness-freelcs /usr/bin/
COPY source_files/Loudness_Correction_Settings.json /etc/
COPY source_files/libinput_sndfile-freelcs.so /usr/lib/
RUN ldconfig
RUN apt-get -y update
RUN apt-get -y install python3 sox mediainfo gnuplot fonts-liberation ffmpeg
CMD ["/usr/bin/python3", "/usr/bin/LoudnessCorrection.py", "-configfile", "/etc/Loudness_Correction_Settings.json" ]
