

This site is used for FreeLCS development and is no interest to normal users of the software.

If you want to download the latest version of this software please visit the main site: http://freelcs.sourceforge.net/



FreeLCS stands for Free Loudness Correction Server. The software lets you easily set up a server that shares one of it's folders to the network where users can drop audio files to be loudness corrected according to the EBU R128 loudness standard. The server also creates a loudness history graphics file which gives visual feedback of the internal loudness variations in a file.

The software is very fast even on modest hardware giving 20 times faster than realtime processing (stereo files) on a server with one Intel Core 2 Duo processor, 2 GB Ram, 3 internal Sata disks in software RAID 0.

FreeLCS uses other open source programs to get the job done (Linux, libebur128, gnuplot, FFmpeg, sox).


Features:

- Calculates loudness according to EBU R128 for files dropped into the HotFolder.
- For each file it creates an loudness history graphics file which gives visual feedback of the loudness variations in the file.
- Creates loudness corrected versions of each file dropped in the servers HotFolder.
- Uses FFmpeg to pre-process files and supports the huge number of file formats FFmpeg supports.
- Supports files with several audio streams. Each stream is demuxed to a separate file and loudness corrected.
- Even video files can dropped in for processing. Audio streams are demuxed from the file and processed.
- Supports channel counts from mono to 5.1.
- Takes advantage of multiple processor cores to run calculations simultaneously.
- Uses a protective limiter to prevent clipping in cases where volume must be increased.
- Automatic file deletion after a set time.
- Possible error messages are emailed to the admin.
- All software is free and Open Source.
- Very easy to use, just drop in your file and copy back the corrected version.
- Easy to integrate in many workflows.
- Modest hardware requirements.
- Written in Python 3.
