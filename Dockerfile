FROM ubuntu:24.04
USER root:root
RUN apt-get -y update
# RUN apt-get -y install python3 sox mediainfo gnuplot fonts-liberation ffmpeg samba
RUN apt-get -y install python3 sox mediainfo gnuplot fonts-liberation ffmpeg
COPY ./LoudnessCorrection.py ./loudness-freelcs HeartBeat_Checker.py /usr/bin/
COPY ./Loudness_Correction_Settings.json /etc/
# COPY ./smb.conf /etc/samba/
COPY ./libinput_sndfile-freelcs.so /usr/lib/
RUN ldconfig
# RUN chmod 755 /usr/bin/LoudnessCorrection.py /usr/bin/loudness-freelcs /usr/bin/HeartBeat_Checker.py ; chmod 644 /etc/Loudness_Correction_Settings.json /etc/samba/smb.conf /usr/lib/libinput_sndfile-freelcs.so
RUN chmod 755 /usr/bin/LoudnessCorrection.py /usr/bin/loudness-freelcs /usr/bin/HeartBeat_Checker.py ; chmod 644 /etc/Loudness_Correction_Settings.json /usr/lib/libinput_sndfile-freelcs.so
RUN useradd -M -s /sbin/nologin freelcs
# RUN echo 'freelcs' | smbpasswd -a freelcs
# EXPOSE 445
USER freelcs
CMD ["/usr/bin/python3", "/usr/bin/LoudnessCorrection.py", "-configfile", "/etc/Loudness_Correction_Settings.json" ]
