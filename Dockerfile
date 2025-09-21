FROM ubuntu:24.04
USER root:root
COPY ./LoudnessCorrection.py ./loudness-freelcs /usr/bin/
COPY ./Loudness_Correction_Settings.json /etc/
COPY ./libinput_sndfile-freelcs.so /usr/lib/
RUN ldconfig
RUN apt-get -y update
RUN apt-get -y install python3 sox mediainfo gnuplot fonts-liberation ffmpeg
CMD ["/usr/bin/python3", "/usr/bin/LoudnessCorrection.py", "-configfile", "/etc/Loudness_Correction_Settings.json" ]
