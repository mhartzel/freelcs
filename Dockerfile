FROM ubuntu:26.04 AS base_ubuntu_image
RUN apt-get -y update
RUN apt-get -y upgrade

FROM base_ubuntu_image AS loudness_correction
USER root:root
RUN apt-get -y update
RUN apt-get -y upgrade
RUN DEBIAN_FRONTEND=noninteractive apt-get -y install python3 sox mediainfo gnuplot fonts-liberation ffmpeg samba python3-requests ca-certificates tzdata
COPY ./LoudnessCorrection.py ./loudness-freelcs ./freelcs_startup_file.sh /usr/bin/
COPY ./LoudnessCorrection_Settings.json /etc/
COPY ./smb.conf /etc/samba/
COPY ./libinput_sndfile-freelcs.so /usr/lib/
RUN ldconfig
RUN chmod 755 /usr/bin/LoudnessCorrection.py /usr/bin/loudness-freelcs /usr/bin/freelcs_startup_file.sh ; chmod 644 /etc/LoudnessCorrection_Settings.json /etc/samba/smb.conf /usr/lib/libinput_sndfile-freelcs.so
RUN useradd -M -s /sbin/nologin freelcs
RUN /bin/bash -c "echo -e 'freelcs\nfreelcs' | smbpasswd -a freelcs"
EXPOSE 445
# USER freelcs
# CMD ["/usr/bin/python3", "/usr/bin/LoudnessCorrection.py", "-configfile", "/etc/LoudnessCorrection_Settings.json" ]
CMD ["/usr/bin/freelcs_startup_file.sh"]

FROM base_ubuntu_image AS progress_report
USER root:root
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
COPY ./progress_report /usr/bin/
COPY ./LoudnessCorrection_Settings.json /etc/
RUN chmod 755 /usr/bin/progress_report ; chmod 644 /etc/LoudnessCorrection_Settings.json
CMD ["/usr/bin/progress_report", "-configfile", "/etc/LoudnessCorrection_Settings.json"]

FROM base_ubuntu_image AS heartbeat_checker
USER root:root
RUN apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
RUN apt-get -y install ca-certificates tzdata
COPY ./heartbeat_checker /usr/bin/
COPY ./LoudnessCorrection_Settings.json /etc/
RUN chmod 755 /usr/bin/heartbeat_checker ; chmod 644 /etc/LoudnessCorrection_Settings.json
CMD ["/usr/bin/heartbeat_checker", "-configfile", "/etc/LoudnessCorrection_Settings.json"]
