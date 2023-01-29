FROM xychelsea/ffmpeg-nvidia

WORKDIR /app

COPY environment.yml .
RUN conda env create -f environment.yml
RUN echo "conda activate Beats2Fun" >> ~/.bashrc
SHELL ["/bin/bash", "--login", "-c"]

USER root
RUN rm -rf /usr/lib/x86_64-linux-gnu/libnvidia* /usr/lib/x86_64-linux-gnu/libcuda* /usr/lib/x86_64-linux-gnu/libnv*
RUN ln -s /usr/local/ffmpeg-nvidia/bin/ffmpeg /usr/bin/ffmpeg && ln -s /usr/local/ffmpeg-nvidia/bin/ffprobe /usr/bin/ffprobe

#COPY requirements.txt .
#RUN pip install -r requirements.txt

COPY ./*.py .
COPY parsers/*.py ./parsers/
COPY Resources ./Resources/

#RUN rm /usr/lib/x86_64-linux-gnu/libnvidia-ml.so.1

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "Beats2Fun", "python", "Beats2Fun.py"]