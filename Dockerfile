FROM --platform=linux/amd64 ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip wget git file dc unzip && rm -rf /var/lib/apt/lists/*

# Install FSL
RUN wget https://fsl.fmrib.ox.ac.uk/fsldownloads/fslinstaller.py && \
    python3 fslinstaller.py -d /usr/local/fsl -q && rm fslinstaller.py
ENV FSLDIR=/usr/local/fsl
ENV PATH=${FSLDIR}/share/fsl/bin:${PATH}
ENV FSLOUTPUTTYPE=NIFTI_GZ

RUN mkdir /input /output /weights /app
COPY requirements.txt /app/
COPY scripts/ /app/scripts/
COPY resources/ /app/resources/

# Install base dependencies
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt

# Install additional necessary dependencies
RUN pip install --no-cache-dir batchgenerators dynamic-network-architectures batchgeneratorsv2 matplotlib seaborn

# Clone and install nnUNet
RUN git clone https://github.com/MIC-DKFZ/nnUNet.git /app/nnUNet && \
    cd /app/nnUNet && \
    pip install -e .

ENV LC_ALL=C.UTF-8
WORKDIR /app
CMD ["python3", "scripts/main.py"]